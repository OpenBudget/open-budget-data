import gzip
import json

if __name__=="__main__":
    out = file('fixtures.json','w')
    for line in file("../budget/budgets.json"):
        line = json.loads(line)
        if line['year'] in [2012, 2013] and (line['code'] == '00' or line['code'].startswith('0020')):
            line['fixture-type'] = 'bl'
            out.write(json.dumps(line)+'\n')
    for line in gzip.GzipFile("../changes/changes_total.json.gz"):
        line = json.loads(line)
        if line['year'] in [2012, 2011] and line['budget_code'].startswith('0020'):
            line['fixture-type'] = 'cl'
            out.write(json.dumps(line)+'\n')

