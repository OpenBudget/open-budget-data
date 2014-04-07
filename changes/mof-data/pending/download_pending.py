#encoding: utf8

import sys
import urllib2
from pyquery import PyQuery as pq

YEAR = 2014

def datagov(x):
  if x.startswith('/'):
    return 'http://data.gov.il%s' % x
  else:
    return x

if __name__ == "__main__":
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
                print 'downloading', href
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
                    filename = '../changes-pending.csv'
                    pending = True
                if 'תאריך אישור' in csvdata:
                    filename = '../changes-%s.csv' % YEAR
                file(filename,'w').write(csvdata)
        for _f in files:
            f = pq(_f)
            href = f.attr('href')
            if href.endswith('zip'):
                print 'downloading', href
                zipdata = urllib2.urlopen(datagov(href)).read()
                if pending:
                    filename = '../../../change_explanation/explanations-pending.zip'
                else:
                    filename = '../../../change_explanation/explanations-%s.zip' % YEAR
                file(filename,'w').write(zipdata)
