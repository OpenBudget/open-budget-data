# encoding: utf8

import json
import re

WORDS = re.compile(u'([א-ת0-9a-zA-Z]+)')
theIndex = {}

class make_search_prefixes(object):

    def index(self,name,kind,year,value):
        splits = WORDS.findall(name)
        subsplits = [ x[1:] for x in splits if x[0] in [u'ה', u'ב', u'ו', u'מ', u'ב', u'כ', u'ל'] and len(x) > 3 ]
        splits.extend(subsplits)
        tokens = set()
        for split in splits:
            tokens.update(set([ split[:l] for l in range(1,len(split)+1) ]))
        key = kind+":"+value+":"+name
        priority = 9999999999
        try:
            priority = int("1"+value)
        except:
            pass
        theIndex.setdefault(key,{'kind':kind,'tokens':list(tokens),'value':value,'year':set(),"priority":priority})['year'].add(year)

    def processBudgets(self,input):
        with open(input) as budgetsFile:
            for line in budgetsFile:
                data = json.loads(line)
                self.index(data['title'],'BudgetLine',data['year'],data['code'])

    def process(self,input,output):
        self.processBudgets(input)
        with open(output,"w") as out:
            for rec in theIndex.values():
                rec['year'] = list(rec['year'])
                out.write(json.dumps(rec)+"\n")
