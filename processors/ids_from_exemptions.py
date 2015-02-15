###encoding: utf8
import json
import bisect
import logging

class ids_from_exemptions(object):

    def process(self,input,output):

        out = file(output,'w')
        for line in file(input):
            data = json.loads(line)
            id = str(data.get('supplier_id','')).strip()
            name = data.get('supplier','').strip()
            if id != '' and name != '':
                ret = {'id':id,'name':name,'kind':''}
                out.write(json.dumps(ret,sort_keys=True)+'\n')
