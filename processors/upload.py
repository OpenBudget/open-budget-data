from gevent import monkey; monkey.patch_all(subprocess=False)
import gevent
from gevent.pool import Pool
from gevent.queue import Queue
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

def do_write(kind,APIKEY,lines,i,good_queue):
    values = "\n".join([ x[0] for x in lines ])
    keys = [ x[1] for x in lines ]
    try:
        req = urllib2.Request('http://the.open-budget.org.il/api/update/%s?apikey=%s' % (kind,APIKEY),
                              values,
                              headers={'Content-type': 'application/x-binary'})
        u = urllib2.urlopen(req).read()
    except Exception,e:
        raise
    logging.debug("do_write: %s,%s" % (u,i))
    good_queue.put(keys)

class upload(object):
    def process(self,input,output,kind,APIKEY):
        pool = Pool(50)

        if APIKEY is None:
            logging.error("no API key")
            return

        conn = sqlite3.connect(input)
        c = conn.cursor()
        dirtys = c.execute("""SELECT value,key from data WHERE dirty = 1""")

        good_queue = Queue()
        def _undirty(queue):
            uploaded = 0
            for keys in queue:
                logging.debug("marking keys %r as valid" % keys)
                c.execute("""UPDATE data SET dirty=0 WHERE dirty=1 and key in (%s)""" %
                             ','.join('?'*len(keys)), keys)
                conn.commit()
                uploaded += len(keys)
            return uploaded

        written = 0
        while True:
            lines = dirtys.fetchmany(5)
            if len(lines) == 0:
                break
            lines = [ (x[0],x[1]) for x in lines ]
            written+=len(lines)

            #lines = "\n".join(lines)
            #print lines
            pool.spawn(do_write, kind, APIKEY, lines, written, good_queue)
            #do_write("\n".join(lines),i)
            #print "."

        undirty = gevent.spawn(_undirty,good_queue)
        pool.join()
        # if i > 0:
        #     dirtys = c.execute("""UPDATE data SET dirty=0 WHERE dirty=1""")
        good_queue.put(StopIteration)
        undirty.join()

        conn.commit()
        conn.close()

        uploaded = undirty.value

        if written != uploaded:
            raise RuntimeError("{2}: Updated less than expected {0} > {1}".format(written,uploaded,input))
        gevent.sleep(1)
        file(output,"w").write("OK")
