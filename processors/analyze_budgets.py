import logging
import csv
import field_convertors
import json
import sys

class Aggregator(object):

    def __init__(self):
        self.short_term_history = {}
        self.explanations = set()
        self.yearcodes = []

    def add_item(self,item):
        explanation = item.get('explanation')
        if explanation is not None:
            self.explanations.add(explanation)
        year = item.get('year',0)
        if year>=2009 and year < 2015:
            self.short_term_history.setdefault(year,[]).append(item)
        self.yearcodes.append((item['year'],item['code']))

    def calc_explanations(self):
        return '<br/>'.join(list(self.explanations))

    def calc_short_term_yearly_change(self):
        totals = [ (sum(xx.get('net_allocated',0) for xx in x), sum(xx.get('net_revised',xx.get('net_allocated',0)) for xx in x)) for x in self.short_term_history.values() ]
        totals = [ (x,y) for x,y in totals if x>0]
        totals = [ (1.0*y)/x for x,y in totals ]
        if len(totals) == 0:
            return None
        ratio = sum(totals)/len(totals)
        ratio = int(100*(ratio-1))
        return ratio

    def get_items(self):
        for year,code in self.yearcodes:
            ret = {
                'year': year,
                'code': code,
                'explanation': self.calc_explanations(),
            }
            if year >= 2014:
                ret['analysis_short_term_yearly_change'] = self.calc_short_term_yearly_change()
            yield ret

class analyze_budgets(object):
    def process(self,input,output,has_header=False,field_definition=[]):

        aggregator = {}

        for line in file(input):
            line = json.loads(line.strip())
            for x in line.get('equiv_code',[]):
                aggregator.setdefault(x,Aggregator()).add_item(line)

        out = file(output,'w')
        for a in aggregator.values():
            for x in a.get_items():
                out.write(json.dumps(x,sort_keys=True)+'\n')

if __name__ == "__main__":
    inputs = sys.argv[1]
    output = sys.argv[2]
    processor = analyze_budgets().process(inputs,output)
