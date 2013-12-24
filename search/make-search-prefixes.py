# encoding: utf8

import json
import re

BUDGET_FN = "../budget/budgets.json"
OUT_FN = "search.json"
WORDS = re.compile(u'([א-ת0-9a-zA-Z]+)')
theIndex = {}

def index(name,kind,year,value):
    splits = WORDS.findall(name)
    subsplits = [ x[1:] for x in splits if x[0] in [u'ה', u'ב', u'ו', u'מ', u'ב', u'כ', u'ל'] and len(x) > 3 ]
    for split in splits + subsplits:
#        prefixes = [ split[:l] for l in range(1,len(split)+1) ]
#        for prefix in prefixes:
        key = kind+":"+split+":"+value
        theIndex.setdefault(key,{'kind':kind,'prefix':split,'value':value,'year':set()})['year'].add(year)

def processBudgets():
    with open(BUDGET_FN) as budgetsFile:
        for line in budgetsFile:
            data = json.loads(line)
            index(data['title'],'BudgetLine',data['year'],data['code'])

if __name__ == "__main__":
    processBudgets()
    with open(OUT_FN,"w") as out:
        for rec in theIndex.values():
            rec['year'] = list(rec['year'])
            out.write(json.dumps(rec)+"\n")
        
