#encoding: utf8
import logging
import csv
import json

if __name__ == "__main__":
    inputs = sys.argv[1:-1]
    output = sys.argv[-1]
    processor = combine_budget_jsons().process(inputs,output)

class combine_budget_jsons(object):

    def process(self,inputs,output):
        alldata = {}
        keys = set()

        for f in inputs:
            logging.debug("combine_budget_jsons: %s" % f)
            for line in file(f):
                try:
                    line = line.strip()
                    rec = json.loads(line)
                    if rec.get('title') == None: continue
                    key = "%s|%10s" % (rec['year'],rec['code'])
                    keys.add(key)
                    alldata.setdefault(key,{}).update(rec)
                except Exception,e:
                    logging.error("combine_budget_jsons: error %s in line %r" % (e,line))

        for year in range(1992,2015):
            totalkey = '%s|%8s' % (year,"00")
            if '%s|%10s' % (year,"00") in keys:
                continue
            totalrec = { 'title'     : u'המדינה',
                         'year'      : year,
                         'code' : '00',
                         }
            for key in keys:
                if '%s|%10s' % (year,"0000") in key:
                    continue
                if key.startswith(totalkey):
                    rec = alldata[key]
                    for k,v in rec.iteritems():
                        if type(v) == int:
                            totalrec[k] = totalrec.setdefault(k,0) + v
            totalrec['year'] = year

            logging.debug('combine_budget_jsons: total for %s = %s' % (year,totalrec))

            alldata.setdefault(totalkey,{}).update(totalrec)
            keys.add(totalkey)


        keys = list(keys)
        keys.sort()

        out = file(output,'w')
        for k in keys:
            out.write( json.dumps(alldata[k],sort_keys=True)+'\n' )
