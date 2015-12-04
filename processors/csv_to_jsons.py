import logging
import csv
import field_convertors
import json

if __name__ == "__main__":
    inputs = sys.argv[1:-1]
    output = sys.argv[-1]
    processor = csv_to_jsons().process(inputs,output)

class csv_to_jsons(object):
    def process(self,input,output,has_header=False,field_definition=[]):
        reader = csv.reader(file(input,"rU"))
        if has_header:
            field_names = reader.next()
            field_names = [ x.decode('utf8').strip() for x in field_names ]
        else:
            field_names = [ x['field_name'] for x in field_definition ]
        field_translations = dict([ (x.get('field_title',x['field_name']),x['field_name']) for x in field_definition ])
        convertors = dict([ (x['field_name'], field_convertors.__dict__[x.get('convertor','id')]) for x in field_definition ])
        out = None
        value_adders = [field for field in field_definition if field.get('value') is not None]
        for row in reader:
            if set(row) == set([""]): continue
            record = dict(zip(field_names,row))
            outrec = {}
            for k,v in record.iteritems():
                k = field_translations.get(k)
                if k is None or k == '_':
                    continue
                convertor = convertors[k]
                try:
                    v = convertor(v.strip())
                except Exception,e:
                    logging.error("%s:%s - %s" % (k,v,e))
                    raise
                outrec[k] = v
            for f in value_adders:
                outrec[f['field_name']] = f['value']
            if out is None:
                out = file(output,"w")
            out.write(json.dumps(outrec,sort_keys=True)+"\n")
        if out is None:
            out = file(output,"w")
