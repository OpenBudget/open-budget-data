#encoding: utf8

import csv
import json
import logging
import sys
import re
import requests
import openpyxl
import datetime
from io import BytesIO
from pyquery import PyQuery as pq

def floater(x):
    if type(x) in (int,long,float):
        return x
    if len(x.strip())==0:
        return None
    try:
       return float(x.encode('utf8').replace(',',''))
    except Exception,e:
       print e
       return None

def utf8(x):
    if type(x) in (int,long,float,datetime.datetime):
        return str(x)
    return x.strip()

def boolean(x):
    return x.strip()==u'כן'

DATE_RE = re.compile('[0-9]+')
def date(x):
    if type(x) is datetime.datetime:
        return x.strftime('%d/%m/%Y')
    elif type(x) in (int,long):
        return (datetime.date(1900,1,1)+datetime.timedelta(days=x)).strftime('%d/%m/%Y')    x=x.strip()
    if len(x)==0:
        return None
    else:
        parts = DATE_RE.findall(x)
        if len(parts)==3:
            day = int(parts[0])
            month = int(parts[1])
            year = int(parts[2])
            if year<100:
                year += 2000
            return '%02d/%02d/%04d' % (day,month,year)
    print repr(x)
    assert(False)

def budget_code(x):
    x=x.strip()
    if len(x)==11:
        x='00'+x.replace('-','')
        assert(len(x)==10)
    elif len(x)==8:
        assert('-' not in x)
        x='00'+x
    elif len(x)==0:
        return None
    else:
        print repr(x)
        assert(False)
    return x

KNOWN_HEADERS = {
    u'ביצוע חשבוניות במטבע מקומי כולל מע"מ והצמדות': ('executed', floater),
    u'ביצוע חשבוניות במטבע מקומי כולל מע"מ והצ': ('executed', floater),
    u'''מס' פנייה במנו"ף/מנור"''': ('manof_ref', utf8),
    u'ערך ההזמנה כולל מע"מ': ('volume', floater),
    u"אופן רכישה": ('purchase_method', utf8),
    u"הזמנה רגישה": ('sensitive_order', boolean),
    u"הזמנת רכש": ('order_id', utf8),
    u"מטבע": ('currency', utf8),
    u"מטרת התקשרות": ('purpose', utf8),
    u"סיבת פטור": ('exemption_reason', utf8),
    u"סיום תקופת תוקף": ('end_date', date),
    u"קבוצה רוכשת": ('purchasing_unit_code', utf8),
    U"קוד ספק": ('supplier_code', utf8),
    u"שם אתר": ('purchasing_unit', utf8),
    u"שם הספק": ('supplier_name', utf8),
    u"שם חברה": ('publisher', utf8),
    u"תאור של ארגון רכש": ('buyer_description', utf8),
    u"תאריך יצירת ההזמנה": ('order_date', date),
    u"תיאור תקנה תקציבית": ('budget_title', utf8),
    u"תקנה תקציבית": ('budget_code', budget_code),
    u"": (None, None),
    u'הבהרות': ('explanation', utf8)
}

def get_all_pages():
    URL="https://foi.gov.il/he/search/site/?f[0]=im_field_mmdtypes%3A368&page={0}"
    page=0
    done = False
    while not done:
        results = requests.get(URL.format(page),verify=False).text
        results = pq(results)
        results = results.find('.search-result')
        for result in results:
            result = pq(result).find('li')
            url = pq(result[0].find('a')).attr('href')
            title = pq(result[0].find('a')).text()
            publisher = pq(result[1]).text()
            date = pq(result[2]).text().replace('.','/')
            yield date, title, publisher, url
        if len(results)==0:
            done = True
        page += 1

def query_foi_gov():
    for date, title, publisher, url in get_all_pages():
        try:
            single = requests.get(url,verify=False).text
            files = pq(single).find('span.file a')
            for a in files:
                href = pq(a).attr('href')
                if not 'xls' in href.lower():
                    continue
                content = requests.get(href,verify=False).content
                yield href, date, title, publisher, BytesIO(content)
        except Exception, e:
            print 'Failed to read file of %r: %r' % (title, e)
            continue

def get_records():
    for href, date, title, publisher, f in query_foi_gov():
        try:
            wb = openpyxl.reader.excel.load_workbook(f, read_only=True, data_only=True)
            ws = wb.worksheets[0]
            data = [[cell.value for cell in row] for row in ws.rows]
            yield href, date, title, publisher, data
        except Exception, e:
            print 'Bad Excel format for %r: %r' % (title, e)
            continue

def process_procurement(out):
    for href, date, title, publisher, data in get_records():
        headers = data[0]
        headers = [h.strip() if h is not None else '' for h in headers]
        try:
            headers = [KNOWN_HEADERS[h] for h in headers]
        except Exception, e:
            if u"הזמנה רגישה" not in headers:
                print 'Bad report format for %r' % title
            else:
                print 'Bad Headers for %r: %r' % (title, e)
            continue

        for row in data[1:]:
            if all(x is None for x in row):
                break
            row = dict(zip(headers,row))
            out_rec = {'report_date':date, 'report_title':title, 'report_publisher':publisher}
            for k,v in row.items():
                out_k, filt = k
                if filt is not None and v is not None:
                    try:
                        out_v = filt(v)
                    except Exception, e:
                        print 'Failed to transform %r for %r in %s' % (v, out_k, href)
                        raise
                    out_rec[out_k] = out_v
            out.write("%s\n" % json.dumps(out_rec))

        print u'Processed successfully %r' % title

class procurement_scraper(object):

    def process(self,input,output):
        process_procurement(open(output,'wb'))

if __name__ == "__main__":
    input = sys.argv[1]
    output = sys.argv[-1]
    procurement_scraper().process(input,output)
