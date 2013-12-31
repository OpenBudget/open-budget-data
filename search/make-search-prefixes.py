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
        
