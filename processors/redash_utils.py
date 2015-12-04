import os
import requests
import re
import logging
import subprocess
import time
import hashlib
import hmac

def sign(key, path, expires):
    if not key:
        return None

    h = hmac.new(str(key), msg=path, digestmod=hashlib.sha1)
    h.update(str(expires))

    return h.hexdigest()

def get_query_results(query_id, secret_api_key, redash_url="http://data.obudget.org"):
    logging.info("Getting Re:dash query {0} with key {1}".format(query_id,secret_api_key))
    path = '/api/queries/{}/results.json'.format(query_id)
    expires = time.time()+900 # expires must be <= 3600 seconds from now
    signature = sign(secret_api_key, path, expires)
    full_path = "{0}{1}?signature={2}&expires={3}&api_key={4}".format(redash_url, path,
                                                                      signature, expires, secret_api_key)
    return requests.get(full_path).json()['query_result']['data']['rows']
