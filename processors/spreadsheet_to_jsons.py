import logging
import json
import urllib2
import field_convertors

if __name__ == "__main__":
    inp,out,key,sheet = sys.argv[1:4]
    processor = spreadsheet_to_jsons().process(inp,out,key,sheet)

class spreadsheet_to_jsons(object):
    def process(self,input,output,key="",sheet=None,num_cols=2,convertors={}):

        sheet = "sheet=%s&" % sheet if sheet is not None else ""
        columns = ",".join([ chr(65+i) for i in range(num_cols) ])
        params = (key,sheet,columns)
        URL="https://docs.google.com/a/open-budget.org.il/spreadsheets/d/%s/gviz/tq?%stq=select+%s&tqx=reqId:1;out:json;+responseHandler:x" % params
        print URL
        data = urllib2.urlopen(URL).read()[2:-2] # remove JavaScript handler
        data = json.loads(data)

        header = [x['label'] for x in data['table']['cols']]
        rows = [[x['v'] for x in data['table']['rows'][i]['c']] for i in range(len(data['table']['rows']))]

        convertors = dict([ (h, field_convertors.__dict__[convertors.get(h,'id')]) for h in header ])
        rows = [ dict([(k,convertors[k](v)) for k,v in zip(header,row)]) for row in rows ]
        out = file(output,'w')
        for row in rows:
            out.write(json.dumps(row,sort_keys=True)+"\n")
