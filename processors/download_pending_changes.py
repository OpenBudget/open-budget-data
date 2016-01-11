#encoding: utf8

import os
import sys
import urllib2
from pyquery import PyQuery as pq
import logging
import hashlib
import sqlite3
import json

YEAR = 2015

def mofgov(relative):
    return "http://www.mof.gov.il"+relative

def write_if_changed(filename,data):
    try:
        current = hashlib.md5(file(filename).read()[:10000]).hexdigest()
        current_size = os.path.getsize(filename)
    except Exception, e:
        print e
        current = None
        current_size = None
    new = hashlib.md5(data[:10000]).hexdigest()
    if current != new and len(data) != current_size:
        logging.debug('>> %s != %s, %s != %s' % (current,new,len(data),current_size))
        logging.debug('>> %s wrote %d bytes' % (filename,len(data)))
        file(filename,"w").write(data)
        return True
    else:
        logging.debug('>> %s unchanged' % filename)
    return False

def download(url,last_modified):
    request = urllib2.Request(url)
    opener = urllib2.build_opener()
    # last_modified_date = last_modified.get(url)
    # if last_modified_date is not None:
    #     request.add_header('If-Modified-Since',last_modified_date)
    datastream = opener.open(request, timeout=60)
    # last_modified[url] = datastream.headers.get('Last-Modified')
    ret = datastream.read()
    if len(ret) == 0:
        return None
    return ret

if __name__ == "__main__":
    inputs = sys.argv[1]
    output = sys.argv[2]
    processor = download_pending_changes().process(input,output)

class download_pending_changes(object):
    def process(self,input,output,changes_basepath,change_expl_basepath,sql_to_delete_from):
        url = mofgov("/BudgetSite/StateBudget/Pages/BudgetChanges.aspx")
        page = urllib2.urlopen(url).read()
        page = pq(page)
        bunches = page(".FilesLinkList")
        downloaded = False
        try:
            last_modified = json.load(file(output))
        except:
            last_modified = {}
        for _bunch in bunches:
            pending = None
            files = pq(_bunch)('a')
            hrefs = [ pq(_f).attr('href') for _f in files ]
            hrefs.sort(key=lambda x: 0 if x.endswith('csv') else 1)
            for href in hrefs:
                if href.endswith('csv'):
                    logging.debug('downloading %s' % href)
                    try:
                        csvraw = download(mofgov(href),last_modified)
                        for coding in ['utf8','iso8859-8','windows-1255']:
                            try:
                                decoded = csvraw.decode(coding)
                                if u'שנה' in decoded:
                                    csvdata = decoded
                                    break
                                else:
                                    decoded = None
                            except:
                                continue
                        csvdata = csvdata.split('\n')
                        while u'שנה' not in csvdata[0]:
                            csvdata.pop(0)
                        csvdata = '\n'.join(csvdata)
                        csvdata = csvdata.encode('utf8')
                    except urllib2.HTTPError, e:
                        if e.code != 304:
                            logging.error('Failed to download %s' % href)
                        else:
                            logging.debug('Not modified!')
                            continue
                    if '/Committee/' in href or 'תאריך משלוח לוועדה' in csvdata:
                        filename = os.path.join(changes_basepath,'changes-pending.csv')
                        logging.info("Setting pending to true")
                        pending = True
                    elif '/Approved/' in href or 'תאריך אישור' in csvdata:
                        filename = os.path.join(changes_basepath,'changes-%s.csv' % YEAR)
                        logging.info("Setting pending to false")
                        pending = False
                    downloaded = downloaded or write_if_changed(filename,csvdata)
                if href.endswith('rar'):
                    logging.debug('downloading %s' % href)
                    try:
                        rardata = download(mofgov(href),last_modified)
                        assert(pending is not None)
                        if pending:
                            filename = os.path.join(change_expl_basepath,'explanations-pending.rar')
                        else:
                            filename = os.path.join(change_expl_basepath,'explanations-%s.rar' % YEAR)
                        logging.debug('>> %s' % filename)
                        downloaded = downloaded or write_if_changed(filename,rardata)
                    except urllib2.HTTPError, e:
                        if e.code != 304:
                            logging.error('Failed to download %s' % href)
                            href = href.replace('.rar','.zip')
                        else:
                            logging.debug('Not modified!')
                            continue
                if href.endswith('zip'):
                    logging.debug('downloading %s' % href)
                    try:
                        zipdata = download(mofgov(href),last_modified)
                        assert(pending is not None)
                        if pending:
                            filename = os.path.join(change_expl_basepath,'explanations-pending.zip')
                        else:
                            filename = os.path.join(change_expl_basepath,'explanations-%s.zip' % YEAR)
                        logging.debug('>> %s' % filename)
                        downloaded = downloaded or write_if_changed(filename,zipdata)
                    except urllib2.HTTPError, e:
                        if e.code != 304:
                            logging.error('Failed to download %s' % href)
                        else:
                            logging.debug('Not modified!')
                            continue

        if downloaded:
            conn = sqlite3.connect(sql_to_delete_from)
            c = conn.cursor()
            ret = c.execute("""delete from data where key like 'year:%d%%'""" % YEAR)
            logging.info("deleted yearly changes from DB %r" % ret)
            conn.commit()
            conn.close()

        file(output,"w").write(json.dumps(last_modified))
