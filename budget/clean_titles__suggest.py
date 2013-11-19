import json
import csv

filenames = [ "financial_report/2000-2008/out.json",
              "financial_report/2009/out.json",
              "history_neto/history.json",
              "2010_planned/out.json",
              "2011_planned/out.json",
              "title_cleaning.json"
              ]

pre_data = {}

for fn in filenames:
    f = file(fn)
    for l in f:
        try:
            rec = json.loads(l)
            code = rec['code']
            year = rec['year']
            title = rec['title']
            pre_data.setdefault(code,{})[year] = title
        except:
            continue

data = {}
for code, titles in pre_data.iteritems():
    for year, title in titles.iteritems():
        data.setdefault(code,{}).setdefault(title,set([])).add(year)

def diffstr(s,t):
    return sum([ 1 if s[x] != t[x] and not (s[x] in "0123456789" or t[x] in "0123456789") else 0 for x in range(min(len(s),len(t))) ]) + abs(len(s)-len(t))

out = csv.writer(file('suggested-clean-titles.csv','w'))

for code, titles in data.iteritems():
    if len(titles.keys()) == 1:
        # only one option for this code, great!
        continue
    lengths = set([ len(x) for x in titles.keys() ])
#    if len(lengths) > 1:
#        # lengths too different
#        continue
    counts = [ (x,len(titles[x])) for x in titles.keys() ]
    maxdiff = 0
    for s in counts:
        for t in counts:
            maxdiff = max(maxdiff,diffstr(s[0],t[0]))
#    if maxdiff > 5:
        # content too different
#        continue
    counts.sort(key=lambda r:r[1],reverse=True)
#    if counts[0][1] == counts [-1][1]:
#        continue
#    print (", ".join(["%s (%s)" % (get_display(x[0]), x[1]) for x in counts]) + " ==> " + get_display(counts[0][0])).encode('utf8')
    out.writerow(sum([[counts[i][0].encode('utf8'),counts[i][1],'?'] for i in range(len(counts))],[code,len(lengths)*maxdiff]))
