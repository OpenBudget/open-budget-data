#encoding: utf8 
import os
import sys
import re
import OleFileIO_PL
from dateutil import parser
import glob
import csv
import gzip

date_re = re.compile('([0-9]+/[0-9]+/[0-9]+)')

def extract(filename):
    out = os.popen("PYTHONPATH= python /Users/adam/code/unoconv/unoconv -T 3 -o tmp.txt -f txt %s" % filename).read()
    txt = file("tmp.txt").read().split('\n')
    end = 0
    start = len(txt)
    date = None
    for i, line in enumerate(txt):
        if 'בברכה' in line: end = i
        if 'בכבוד רב' in line: end = i
        if 'הנדון' in line: start = i
        dates = date_re.findall(line)
        if len(dates) > 0:
            date = dates[0]
    if date is None:
        ole = OleFileIO_PL.OleFileIO(filename)
        meta = ole.get_metadata()
        date = meta.last_saved_time
    else:
        date = parser.parse(date)
    explanation = None
    if start < end:
        explanation = "".join( txt[start+1:end] ).decode('utf8')
    return date, explanation
    

if __name__=="__main__":
    all_docs = glob.glob("*.doc")

    def rows():
        for i,filename in enumerate(all_docs):
            parts = filename.split(".")[0].split("_")
            parts = map(int,parts)
            year,req_pri,req_sec = parts
            for x in range(3):
                try:
                    date, explanation = extract(filename)
                    row = [year,req_pri,req_sec,date.strftime("%d/%m/%Y"),explanation.encode('utf8')]
                    if explanation is None: print filename, row
                    yield row
                    print filename,"OK"
                except KeyboardInterrupt, e2:
                    print "KeyboardInterrupt"
                    continue
                except Exception, e:
                    print filename,"ERR"
                    print e
                    continue
                break
            if i%10 == 0: 
                print i,"/",len(all_docs)

    csv.writer(gzip.GzipFile('explanations.csv.gz','w')).writerows(rows())
