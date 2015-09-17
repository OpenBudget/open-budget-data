#encoding: utf8

import os
import sys
import requests
import hashlib
import json

class download_if_changed(object):
    def process(self,input,output,url,filename):
        data = requests.get(url).content
        data_hash = hashlib.md5(data).hexdigest()
        current = ""
        try:
            current = file(filename).read()
        except:
            pass
        current_hash = hashlib.md5(current).hexdigest()
        if current_hash != data_hash:
            file(filename,'w').write(data)
        file(output,'w').write('OK')
