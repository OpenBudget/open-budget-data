from gevent import monkey; monkey.patch_socket() ; monkey.patch_ssl()
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

        to_write = 0
        uploaded = 0

        good_queue = Queue()
        def _undirty(queue):
            global uploaded
            for keys in queue:
                logging.debug("marking keys %r as valid" % keys)
                c.execute("""UPDATE data SET dirty=0 WHERE dirty=1 and key in (%s)""" %
                             ','.join('?'*len(keys)), keys)
                conn.commit()
                uploaded += len(keys)
        undirty = gevent.spawn(_undirty,good_queue)

        while True:
            lines = dirtys.fetchmany(5)
            if len(lines) == 0:
                break
            lines = [ (x[0],x[1]) for x in lines ]
            to_write+=len(lines)

            #lines = "\n".join(lines)
            #print lines
            pool.spawn(do_write, kind, APIKEY, lines, to_write, good_queue)
            #do_write("\n".join(lines),i)
            #print "."
        pool.join()
        # if i > 0:
        #     dirtys = c.execute("""UPDATE data SET dirty=0 WHERE dirty=1""")
        good_queue.put(StopIteration)
        undirty.join()

        conn.commit()
        conn.close()

        if to_write != uploaded:
            raise RuntimeError("Updated less than expected {0} > {1}".format(to_write,uploaded))
        gevent.sleep(1)
        file(output,"w").write("OK")
