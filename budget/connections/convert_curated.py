import sys
import csv
import re
import json
import pprint

CODE = re.compile('C((?:[0-9][0-9])+)')

if __name__ == "__main__":
    out = []
    for row in csv.reader(file(sys.argv[1])):
        try:
            year = int(row[0])
            prevyear = year-1
            code = CODE.findall(row[1])[0]
            equivs = CODE.findall(row[4])
            if len(equivs) == 0:
                continue
            out.append( [[year,code],[[prevyear,c] for c in equivs]])
        except:
            continue
    pprint.pprint(out)
    file(sys.argv[2],'w').write(json.dumps(out))
