#encoding: utf8

import os
import sys
import urllib2
from pyquery import PyQuery as pq
import logging
import hashlib

YEAR = 2014

def datagov(x):
  if x.startswith('/'):
    return 'http://data.gov.il%s' % x
  else:
    return x

def write_if_changed(filename,data):
    try:
        current = hashlib.md5(file(filename).read()).hexdigest()
    except:
        current = None
    new = hashlib.md5(data).hexdigest()
    if current != new:
        logging.debug('>> %s wrote %d bytes' % (filename,len(data)))
        file(filename,"w").write(data)
    else:
        logging.debug('>> %s unchanged' % filename)

if __name__ == "__main__":
    inputs = sys.argv[1]
    output = sys.argv[2]
    processor = download_pending_changes().process(input,output)

class download_pending_changes(object):
    def process(self,input,output,changes_basepath,change_expl_basepath):
        ids = ["753", "754"]
        for id in ids:
            url = datagov("/dataset/%s" % id)
            page = urllib2.urlopen(url).read()
            page = pq(page)
            files = page(".file a")
            pending = False
            for _f in files:
                f = pq(_f)
                href = f.attr('href')
                if href.endswith('csv'):
                    logging.debug('downloading %s' % href)
                    csvdata = urllib2.urlopen(datagov(href)).read()
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
                    if 'תאריך משלוח לוועדה' in csvdata:
                        filename = os.path.join(changes_basepath,'changes-pending.csv')
                        pending = True
                    if 'תאריך אישור' in csvdata:
                        filename = os.path.join(changes_basepath,'changes-%s.csv' % YEAR)
                    write_if_changed(filename,csvdata)
            for _f in files:
                f = pq(_f)
                href = f.attr('href')
                if href.endswith('zip'):
                    logging.debug('downloading %s' % href)
                    zipdata = urllib2.urlopen(datagov(href)).read()
                    if pending:
                        filename = os.path.join(change_expl_basepath,'explanations-pending.zip')
                    else:
                        filename = os.path.join(change_expl_basepath,'explanations-%s.zip' % YEAR)
                    logging.debug('>> %s' % filename)
                    write_if_changed(filename,zipdata)
                if href.endswith('rar'):
                    logging.debug('downloading %s' % href)
                    rardata = urllib2.urlopen(datagov(href)).read()
                    if pending:
                        filename = os.path.join(change_expl_basepath,'explanations-pending.rar')
                    else:
                        filename = os.path.join(change_expl_basepath,'explanations-%s.rar' % YEAR)
                    logging.debug('>> %s' % filename)
                    write_if_changed(filename,rardata)

        file(output,"w").write("OK")
