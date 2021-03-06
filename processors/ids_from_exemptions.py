###encoding: utf8
import json
import bisect
import logging

class ids_from_exemptions(object):

    allowed_prefixes = [
        '0', '1', '2', '3', '4', '6', '8', '9',
        '57', '590', '589',
        '53', '54', '55',
        '598', '599',
        '5792', '5793',
        '5892', '5893',
        '5624', '5625', '5626', '5627',
        '5636', '5631', '5632', '5634',
        '5621', '5623',
    ]

    def legal_id(self, id, name):
        if len(id)>9: return False
        valid = sum( int(x) for x in ''.join( str((i%2+1)*int(x)) for i,x in enumerate(id) ) ) % 10 == 0
        return (id != '' and
                name != '' and
                valid and
                any(id.startswith(x) for x in self.allowed_prefixes))

    def process(self,input,output):

        out = file(output,'w')
        for line in file(input):
            data = json.loads(line)
            supplier_id = data.get('supplier_id')
            if supplier_id is None: continue
            id = str(supplier_id).strip()
            id = "0" * max(0,9-len(id)) + id
            name = data.get('supplier','').strip()
            if self.legal_id(id, name):
                ret = {'id':id,'name':name,'kind':''}
                out.write(json.dumps(ret,sort_keys=True)+'\n')
