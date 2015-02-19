###encoding: utf8
import json
import bisect
import logging

class ids_from_exemptions(object):

    def process(self,input,output):

        out = file(output,'w')
        for line in file(input):
            data = json.loads(line)
            supplier_id = data.get('supplier_id')
            if supplier_id is None: continue
            id = str(supplier_id).strip()
            name = data.get('supplier','').strip()
            if id != '' and name != '' and len(id)>7:
                ret = {'id':id,'name':name,'kind':''}
                out.write(json.dumps(ret,sort_keys=True)+'\n')
