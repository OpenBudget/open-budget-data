#encoding: utf8

import os
import sys
import urllib2
from pyquery import PyQuery as pq
import logging
import hashlib
import sqlite3
import json

YEAR = 2014

def mofgov(relative):
    return "http://www.mof.gov.il"+relative

def write_if_changed(filename,data):
    try:
        current = hashlib.md5(file(filename).read()).hexdigest()
    except:
        current = None
    new = hashlib.md5(data).hexdigest()
    if current != new:
        logging.debug('>> %s wrote %d bytes' % (filename,len(data)))
        file(filename,"w").write(data)
        return True
    else:
        logging.debug('>> %s unchanged' % filename)
    return False

def download(url,last_modified):
    request = urllib2.Request(url)
    opener = urllib2.build_opener()
    last_modified_date = last_modified.get(url)
    if last_modified_date is not None:
        request.add_header('If-Modified-Since',last_modified_date)
    datastream = opener.open(request, timeout=60)
    last_modified[url] = datastream.headers.get('Last-Modified')
    ret = datastream.read()
    if len(ret) < 1024:
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
        files = page("#ctl00_PlaceHolderMain_GovXContentSectionPanel a")
        pending = False
        downloaded = False
        try:
            last_modified = json.load(file(output))
        except:
            last_modified = {}
        for _f in files:
            f = pq(_f)
            href = f.attr('href')
            if href.endswith('csv'):
                logging.debug('downloading %s' % href)
                try:
                    csvdata = download(mofgov(href),last_modified)
                    for coding in ['utf8','iso8859-8','windows-1255']:
                        try:
                            decoded = csvdata.decode(coding)
                            if u'שנה' in decoded:
                                csvdata = decoded.encode('utf8')
                                break
                            else:
                                decoded = None
                        except:
                            continue
                except urllib2.HTTPError, e:
                    if e.code != 304:
                        logging.error('Failed to download %s' % href)
                    else:
                        logging.debug('Not modified!')
                        continue
                if 'תאריך משלוח לוועדה' in csvdata:
                    filename = os.path.join(changes_basepath,'changes-pending.csv')
                    pending = True
                if 'תאריך אישור' in csvdata:
                    filename = os.path.join(changes_basepath,'changes-%s.csv' % YEAR)
                downloaded = downloaded or write_if_changed(filename,csvdata)
            if href.endswith('rar'):
                logging.debug('downloading %s' % href)
                try:
                    rardata = download(mofgov(href),last_modified)
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
