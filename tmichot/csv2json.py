import csv
import json
import gzip

out = gzip.GzipFile('tmichot.jsons.gz','w')
titles = ["year", "_", "subject", "code", "recepient", "kind", "title", "num_used", "amount_allocated", "amount_supported"]
for line in csv.reader(file('scraping/tmichot.csv')):
    line = zip(titles, line)
    line = dict(line)
    del line["_"]
    line['year'] = int(line['year'])
    line['num_used'] = int(line['num_used'])
    line['amount_supported'] = int(line['amount_supported'])
    line['amount_allocated'] = int(line['amount_allocated'])
    out.write(json.dumps(line)+"\n")

