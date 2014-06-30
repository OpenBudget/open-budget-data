#encoding: utf8
#!/usr/bin/env python
import sqlite3
import sys
import csv
import json

fields = [
    ("amount_allocated", u"סכום מאושר"),
    ("amount_supported", u"סכום ביצוע"),
    ("code", u"תקנה תקציבית"),
    ("kind", u"סוג תמיכה"),
    ("ngo_id", u"מספר עמותה"),
    ("num_used", u"מספר נתמכים"),
    ("recipient", u"שם ארגון"),
    ("subject", u"נושא"),
    ("title", u"כותרת"),
    ("year", u"שנה"),
]

if __name__ == "__main__":
    dbfile = sys.argv[1]

    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    values = c.execute("""SELECT value FROM data WHERE value like '%ngo_id%'""")
    o = csv.DictWriter(file("export_ngos.csv","w"), [f[0] for f in fields])
    o.writerow(dict((x,y.encode('utf8')) for x,y in fields))
    for value in values:
        j = json.loads(value[0])
        row = {}
        for k,v in j.iteritems():
            if k not in [f[0] for f in fields]: continue
            if type(v)==unicode:
                row[k] = v.encode('utf8')
            else:
                row[k] = v
        o.writerow(row)

    conn.close()
