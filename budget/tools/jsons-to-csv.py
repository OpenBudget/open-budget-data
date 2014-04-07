import unicodecsv
import json

if __name__=="__main__":
    fieldnames=["code","year","title","net_allocated","gross_allocated","net_revised","gross_revised","net_used","gross_used"]
    out = unicodecsv.DictWriter(file('budgets.csv','w'),fieldnames=fieldnames)
    infile = file('budgets.json')
    for line in infile:
        item = json.loads(line)
        out.writerow(item)


        
