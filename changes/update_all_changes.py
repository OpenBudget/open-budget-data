#from gevent import monkey; monkey.patch_socket()
#import gevent
#from gevent.pool import Pool
import json
import urllib2
import sys
import gzip

def do_write(data,i):
    u="BAD"
    try:
        u = urllib2.urlopen('http://the.open-budget.org.il/api/update/cl', data).read()
    except Exception,e: 
        print e
    print u,i

if __name__=="__main__":
    #pool = Pool(1)
    lines = []
    years = [ int(x) for x in sys.argv[1:] ]
    i = 0
    for line in gzip.GzipFile("changes_total.json.gz"):
        if not json.loads(line)['year'] in years:
            print "skipping"
            continue
        lines.append(line.strip())
        if len(lines) == 100:
            #pool.spawn(do_write, "\n".join(lines),i)
            do_write("\n".join(lines),i)
            lines = []
            print "."
        i+=1
    if len(lines)>0:
        do_write("\n".join(lines),i)
    #pool.join()
