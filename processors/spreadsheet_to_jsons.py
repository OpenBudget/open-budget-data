import logging
import json
import requests
import time
import field_convertors
import os
import subprocess
import sys
import urllib3
urllib3.disable_warnings()

def work(input,output,key="",sheet=None,num_cols=2,convertors={},
         spreadsheet_name_key=None,spreadsheet_index_key=None):
    if sheet is None:
        sheets = [ None ]
    else:
        if type(sheet) is str or type(sheet) is unicode:
            sheets = [ sheet ]
        else:
            sheets = sheet
    outdata = ""
    for sheet in sheets:
        sheetp = "sheet=%s&" % sheet if sheet is not None else ""
        columns = ",".join([ chr(65+i) for i in range(num_cols) ])
        params = (key,sheetp,columns)
        URL="https://docs.google.com/a/open-budget.org.il/spreadsheets/d/%s/gviz/tq?%stq=select+%s&tqx=reqId:1;out:json;+responseHandler:x" % params
        print URL
        retries = 3
        while retries > 0:
            try:
                user_agent = {'User-agent': 'Mozilla/5.0', 'Connection':'Close'}
                data = requests.get(URL,headers=user_agent) # remove JavaScript handler
                print data
                data = data.text[data.text.index('{'):-2]
                break
            except Exception,e:
                logging.error("Failed to open url, retries=%d (%s)" % (retries, str(e)))
            time.sleep(10)
            retries = retries - 1
            assert(retries > 0)
        data = json.loads(data)

        header = [x['label'] for x in data['table']['cols']]
        start=0
        if list(set(header))[0] == "":
            header = [x['v'] if x is not None else None for x in data['table']['rows'][0]['c']]
            start = 1
        rows = [[x['v'] if x is not None else None for x in data['table']['rows'][i]['c']] for i in range(start,len(data['table']['rows']))]

        _convertors = dict([ (h, field_convertors.__dict__[convertors.get(h,'id')]) for h in header ])
        rows = [ dict([(k,_convertors[k](v)) for k,v in zip(header,row)]) for row in rows ]
        if spreadsheet_name_key is not None and sheet is not None:
            for row in rows:
                row[spreadsheet_name_key] = sheet
        if spreadsheet_index_key is not None:
            for i,row in enumerate(rows):
                row[spreadsheet_index_key] = i
        if len(rows) > 0:
            outdata += "".join(json.dumps(row,sort_keys=True)+"\n" for row in rows)
    currentdata = ""
    try:
        currentdata = file(output).read()
    except:
        pass
    if outdata != currentdata:
        out = file(output,'w')
        out.write(outdata)
    else:
        os.utime(output, None)

if __name__ == "__main__":
    jargs = [json.loads(x) for x in sys.argv[1:9]]
    inp,out,key,sheet,num_cols,convertors,spreadsheet_name_key,spreadsheet_index_key = jargs[:]
    work(inp,out,key,sheet,num_cols,convertors,spreadsheet_name_key,spreadsheet_index_key)
    sys.exit(0)

class spreadsheet_to_jsons(object):
    def process(self,input,output,key="",sheet=None,num_cols=2,convertors={},
                spreadsheet_name_key=None,spreadsheet_index_key=None):
        env = os.environ.copy()
        cwd = os.getcwd()
        args = ['/usr/bin/env', 'python', __file__]
        jargs = [input,output,key,sheet,num_cols,convertors,spreadsheet_name_key,spreadsheet_index_key]
        jargs = [json.dumps(arg) for arg in jargs]
        args.extend(jargs)
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
