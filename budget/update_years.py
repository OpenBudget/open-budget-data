from gevent import monkey; monkey.patch_socket()
import gevent
from gevent.pool import Pool
import json
import urllib2
import sys

APIKEY = sys.argv[1]

def do_write(data,i):
    u="BAD"
    try:
        req = urllib2.Request('http://the.open-budget.org.il/api/update/bl?apikey=%s' % APIKEY, data, headers={'Content-type': 'application/x-binary'})
        u = urllib2.urlopen(req).read()
    except Exception,e: 
        print e
    print u,i

if __name__=="__main__":
    pool = Pool(10)
    lines = []
    years = [ int(x) for x in sys.argv[2:] ]
    i = 0
    for line in file("budgets.json"):
        if not json.loads(line)['year'] in years and len(years)>0:
            continue
        lines.append(line.strip()+"\n")
        if len(lines) == 25:
            pool.spawn(do_write, "".join(lines),i)
            lines = []
            print "."
        i+=1
    if len(lines)>0:
        do_write("".join(lines),i)
    pool.join()
