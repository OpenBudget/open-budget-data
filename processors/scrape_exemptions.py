#encoding: utf8
import os
import subprocess
import logging
import shutil

class scrape_exemptions(object):

    def process(self,input,output,since='last_week',success_output=None,PROXY=None):
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
        os.mkdir(os.path.join(cwd,output_dir))
        shutil.copyfile(success_output,output)
        args = ['/usr/bin/env', 'python', 'exemption_updated_records_scraper.py',
                '--scrape=%s' % since, output_dir,'--update']
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
        assert(len(stderr.strip())==0)
        shutil.copyfile(output,success_output)
