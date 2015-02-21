#encoding: utf8
import os
import subprocess
import logging
import shutil

class scrape_exemptions(object):

    def process(self,input,output,since='yesterday',PROXY=None):
        env = os.environ.copy()
        if PROXY is not None:
            env['PROXY'] = PROXY
        output_dir = 'intermediates'
        cwd = 'tenders'
        try:
            shutil.rmtree(os.path.join(cwd,output_dir))
        except:
            logging.debug("Didn't delete old dir, whatever")
            pass
        scraper = subprocess.Popen(['/usr/bin/env',
                                  'python',
                                  'exemption_updated_records_scraper.py',
                                  '--scrape=%s' % since,
                                  output_dir,'--update'],
                                  cwd=cwd,env=env,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        stdout, stderr = scraper.communicate()
        for x in stdout.split('\n'):
            logging.debug(x)
        for x in stderr.split('\n'):
            logging.error(x)
        assert(len(stderr.strip())==0)
