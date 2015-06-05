import os
import requests
import re
import logging
import subprocess
import time
import hashlib
import hmac

class download_redash_results(object):

    def sign(self, key, path, expires):
        if not key:
            return None

        h = hmac.new(str(key), msg=path, digestmod=hashlib.sha1)
        h.update(str(expires))

        return h.hexdigest()

    def get_query(self, redash_url, query_id, secret_api_key):
        path = '/api/queries/{}/results.json'.format(query_id)
        expires = time.time()+900 # expires must be <= 3600 seconds from now
        signature = self.sign(secret_api_key, path, expires)
        full_path = "{0}{1}?signature={2}&expires={3}".format(redash_url, path,
                                                              signature, expires)

        return requests.get(full_path).json()['query_result']['data']['rows']

    def process(self,input,output,query_id,api_key):

        rows = self.get_query('http://data.obudget.org', query_id, api_key)

        out = file(output,'w')
        for row in rows:
            out.write(json.dumps(row)+'\n')
