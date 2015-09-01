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
                    if rec.get('title') is not None and rec.get('title','').strip()=="":
                        del rec['title']
                    rec.setdefault('equiv_code',[])
                    key = "%s|%10s" % (rec['year'],rec['code'])
                    keys.add(key)
                    alldata.setdefault(key,{})
                    for k,v in rec.iteritems():
                        if type(v) == str or type(v) == unicode:
                            alldata[key].setdefault(k,'')
                            if not alldata[key][k].startswith(v): # if new data is not a prefix of current data
                                alldata[key][k] = v
                        elif type(v) == int or type(v) == long:
                            alldata[key].setdefault(k,0)
                            if v != 0:
                                alldata[key][k] = v
                        else:
                            if v is not None:
                                alldata[key][k] = v
                except Exception,e:
                    logging.error("combine_budget_jsons: error %s in line %r" % (e,line))

        for year in range(1992,2017):
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
            if alldata[k].get('title') is None:
                continue
            if alldata[k].get('net_allocated') is None:
                continue
            out.write( json.dumps(alldata[k],sort_keys=True)+'\n' )
