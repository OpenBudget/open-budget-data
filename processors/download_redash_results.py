import logging
import json
import redash_utils as rd

class download_redash_results(object):

    def process(self,input,output,query_id,api_key):

        rows = rd.get_query_results(query_id, api_key)

        out = file(output,'w')
        for row in rows:
            out.write(json.dumps(row,sort_keys=True)+'\n')
