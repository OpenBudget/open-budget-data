#encoding: utf8
import os
import subprocess
import logging

class scrape_exemptions(object):

    def process(self,input,output,since='yesterday',PROXY=None):
        env = os.environ.copy()
        if PROXY is not None:
            env['PROXY'] = PROXY
        scraper = subprocess.Popen(['/usr/bin/env',
                                  'python',
                                  'exemption_updated_records_scraper.py',
                                  '--scrape=%s' % since,
                                  'intermediates','--update'],
                                  cwd='tenders',env=env, shell=True,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        stdout, stderr = scraper.communicate()
        for x in stdout.split('\n'):
            logging.debug(x)
        for x in stderr.split('\n'):
            logging.error(x)
