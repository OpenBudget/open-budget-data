import logging
import json
import redash_utils as rd

class combine_redash_results(object):

    def process(self,input,output,combined_field,id_fields):

        queries = [ json.loads(l.strip()) for l in file(input) ]

        out = {}
        for query in queries:
            rows = rd.get_query_results(str(int(query['id'])).strip(), query['api_key'].strip())
            for row in rows:
                ids = [ unicode(row[f]) for f in id_fields ]
                key = "/".join(ids)
                rec = out.setdefault(key,{combined_field:{}})
                existing_keys = rec[combined_field].keys()
                for k,v in row.iteritems():
                    if k in id_fields:
                        rec[k] = v
                    elif k not in existing_keys :
                        rec[combined_field][k] = v
                    else:
                        logging.error('duplicate field: %s in query %r' % (k,query))

        of = file(output,'w')
        for rec in out.values():
            of.write(json.dumps(rec,sort_keys=True)+'\n')
