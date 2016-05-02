#encoding: utf8
import os
import subprocess
import logging
import shutil

class scrape_tenders(object):

    def process(self,input,output,since='last_week',PROXY=None):
        env = os.environ.copy()
        if PROXY is not None:
            env['PROXY'] = PROXY
        cwd = 'tenders'
        int_output = 'processed-tenders.json'
        args = ['/usr/bin/env', 'python', 'tenders_scraper.py',
                int_output, '--since=%s' % since]
        logging.info("RUNNING %s" % " ".join(args))
        logging.info("cwd='%s'" % cwd)
        scraper = subprocess.Popen(args,
                                   cwd=cwd,env=env,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout, stderr = scraper.communicate()
        for x in stdout.split('\n'):
            logging.debug(x)
        for x in stderr.split('\n'):
            logging.error(x)
        if len(stderr.strip())>0:
            raise RuntimeError(stderr.strip())
        shutil.copyfile(os.path.join('tenders',int_output),output)
