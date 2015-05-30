from gevent import monkey; monkey.patch_socket()
import gevent
from gevent.pool import Pool
import json
import urllib2
import sys
import gzip
import sqlite3
import logging

if __name__ == "__main__":
    inputs = sys.argv[1]
    output = sys.argv[2]
    processor = upload().process(input,output)

def do_write(kind,APIKEY,data,i):
    u="BAD"
    try:
        req = urllib2.Request('http://the.open-budget.org.il/api/update/%s?apikey=%s' % (kind,APIKEY), data, headers={'Content-type': 'application/x-binary'})
        u = urllib2.urlopen(req).read()
    except Exception,e:
        raise
    logging.debug("do_write: %s,%s" % (u,i))

class upload(object):
    def process(self,input,output,kind,APIKEY):
        pool = Pool(50)

        if APIKEY is None:
            logging.error("no API key")
            return

        conn = sqlite3.connect(input)
        c = conn.cursor()
        dirtys = c.execute("""SELECT value from data WHERE dirty = 1""")

        i = 0
        while True:
            lines = dirtys.fetchmany(5)
            if len(lines) == 0:
                break
            lines = [ x[0] for x in lines ]
            i+=len(lines)

            lines = "\n".join(lines)
            #print lines
            pool.spawn(do_write, kind, APIKEY, lines,i)
            #do_write("\n".join(lines),i)
            #print "."
        pool.join()
        if i > 0:
            dirtys = c.execute("""UPDATE data SET dirty=0 WHERE dirty=1""")

        conn.commit()
        conn.close()

        gevent.sleep(1)
        file(output,"w").write("OK")
