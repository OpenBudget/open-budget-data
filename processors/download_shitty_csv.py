import os
import requests
import re
import logging

class download_shitty_csv(object):

    def process(self,input,output,url=""):

        repl1 = re.compile(",[\r\n\t ]+(?=[^5])")
        repl2 = re.compile("[\r\n\t ]+,")
        repl3 = re.compile("[\r\n]+(?=[^5])")

        logging.debug("URL: <%s>" % url)
        data = requests.get(url).content
        file(output+".orig","w").write(data)
        logging.debug("Got %d bytes" % len(data))
        l = 0
        while len(data) != l:
            l = len(data)
            data = repl1.sub(",",data)
            data = repl2.sub(",",data)
            data = repl3.sub(" ",data)
            logging.debug("%s < %d" % (output,l))

        file(output,"w").write(data)
