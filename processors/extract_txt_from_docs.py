#encoding: utf8

import zipfile
import os
import gzip
import json
import tempfile
import logging

if __name__ == "__main__":
    input = sys.argv[1:-1]
    output = sys.argv[-1]
    processor = extract_txt_from_docs().process(input,output)

def extract(data):
    file("tmp.doc","w").write(data)
    out = os.popen("PYTHONPATH= python processors/unoconv -T 3 -o tmp.txt -f txt tmp.doc").read()
    txt = file("tmp.txt").read().split('\n')
    end = 0
    start = len(txt)
    for i, line in enumerate(txt):
        if 'בברכה' in line: end = i
        if 'בכבוד רב' in line: end = i
        if 'הנדון' in line: start = i
    explanation = None
    if start < end:
        explanation = "\n".join( txt[start+1:end] ).decode('utf8')
    return explanation


class extract_txt_from_docs(object):
    def process(self,input,output):
        tmp_outfile = tempfile.mktemp()
        out = gzip.GzipFile(tmp_outfile,"w")
        inp = zipfile.ZipFile(file(input))
        names = inp.namelist()
        for filename in names:
            if not filename.endswith('.doc'):
                print filename
                continue
            parts = filename.split("/")[-1].split(".")[0].split("_")
            parts = map(int,parts)
            year,leading_item,req_code = parts
            explanation = extract(inp.read(filename))
            row = {'year':year,'leading_item':leading_item,'req_code':req_code,'explanation':explanation}
            if explanation is None:
                logging.debug("no explanation for %s, %s" % (filename, row))
            else:
                logging.debug("%d / %02d-%03d got %d bytes" % (year,leading_item,req_code,len(explanation)))
            out.write(json.dumps(row)+"\n")

        out.close()
        os.rename(tmp_outfile,output)
