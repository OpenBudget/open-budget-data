#encoding: utf8

from gevent import monkey; monkey.patch_socket()
import gevent
import gzip
import time
import itertools
from gevent.pool import Pool
import urllib2
import os

def get_protocol(t):
    filename = "%04d-%02d-%02d-%02d.rtf" % t
    if os.path.isfile(filename):
        print filename+" VV"
        return
    if os.path.isfile("errs/"+filename):
        print filename+" VX"
        return
    if os.path.isfile(filename+".empty"):
        print filename+" VE"
        return
    time.sleep(4)
    url = "http://www.knesset.gov.il/protocols/data/rtf/ksafim/"+filename
    try:
        data = urllib2.urlopen(url).read()
    except urllib2.HTTPError, e:
        print filename+" XH"
        out = file("errs/"+filename,"w")
        out.write("")
        out.close()
        return
    except Exception, e:
        print filename+" XX "+str(e)
        return
    print filename
    out = file(filename,"w")
    out.write(data)
    out.close()


if __name__=="__main__":
    pool = Pool(4)
    for t in itertools.product(xrange(2005,2014),xrange(1,13),xrange(1,32),xrange(1,6)):
        pool.spawn(get_protocol,t)
    pool.join()


