import logging
import csv
import field_convertors
import json

if __name__ == "__main__":
    inputs = sys.argv[1:-1]
    output = sys.argv[-1]
    processor = analyze_budgets().process(inputs,output)

class Aggregator(object):

    def __init__(self):
        self.short_term_history = {}
        self.explanations = {}

    def add_item(self,item):
        explanation = item.get('explanation')
        if explanation is not None:
            self.explantions.append(explanation)
        year = item.get('year',0)
        if year>=2009 && year < 2015:
            self.short_term_history.setdefault(year,[]).append(item)

    def calc_explanations(self):
        return '<br/>'.join(self.explanations)

    def calc_short_term_yearly_change(self):
        totals = [ sum(xx.get('net_allocated') for xx in x), sum(xx.get('net_revised') for xx in x) for x in self.short_term_history.values() ]
        totals = [ (1.0*y)/x for x,y in totals ]
        ratio = sum(totals)/len(totals)
        ratio = int(100*(ratio-1))
        return ratio

    def get_item(self):
        ret = {
            'explanation': self.calc_explanations(),
            'analysis_short_term_yearly_change': self.calc_short_term_yearly_change()
        }

class analyze_budgets(object):
    def process(self,input,output,has_header=False,field_definition=[]):

        aggregator = {}

        for line in file(input):
            line = json.loads(line.strip())
            for x in line.get('equivs',[]):
                aggregator.setdefault(x,Aggregator()).add_item(x)

        out = file(output,'w')
        for a in aggregator.values():
            out.write(json.dumps(a.get_item(),sort_keys=True))
