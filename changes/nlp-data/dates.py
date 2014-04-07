import csv
import json

if __name__=="__main__":
    r = csv.DictReader(file('budgetRequestIndex.csv'))
    out = file('nlp-dates.jsons','w')
    for l in r:
        if int("0"+l['approvalYear'])<2005: continue

        try:
            date = [ l[x] for x in ['approvalDay','approvalMonth','approvalYear'] ]
            date = "/".join(date)
            budget_code = "%08d" % int(l['programCode'])

            rec = { 'year': int(l['year']),
                    'leading_item':int(l['leadingClause']),
                    'req_code':int(l['requestId']),
                    'budget_code':budget_code,
                    'date/approved-approx': date }
            # key = "/".join([str(int(l[x])) for x in ['year','leadingClause','requestId','programCode']])
            # out[key] = date
            out.write(json.dumps(rec,sort_keys=True)+'\n')
        except Exception,e:
            print e.message
            continue
    #json.dump(out,file('dates.json','w'))
