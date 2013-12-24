from gevent import monkey; monkey.patch_socket()
import gevent
from gevent.pool import Pool
import json
import urllib2
import sys

def do_write(data,i):
    u="BAD"
    #u = urllib2.urlopen('http://the.open-budget.org.il/api/update/bl', data).read()
    u = urllib2.urlopen('http://localhost:8080/api/update/bl', data).read()
    print u,i

if __name__=="__main__":
    pool = Pool(4)
    lines = []
    years = [ int(x) for x in sys.argv[1:] ]
    i = 0
    for line in file("budgets.json"):
        if not json.loads(line)['year'] in years:
            continue
        lines.append(line.strip())
        if len(lines) == 100:
            pool.spawn(do_write, "\n".join(lines),i)
            lines = []
        i+=1
    if len(lines)>0:
        do_write("\n".join(lines),i)
    pool.join()
