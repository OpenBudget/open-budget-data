import sys
import json

class prepare_compare_record(object):
    def process(infile,outfile,year=2015):
        current_recs = []
        recs_by_code = {}
        prev_recs_by_code = {}
        for line in file(infile):
            try:
                rec = json.loads(line.strip())
            except:
                print "%r" % line.strip()
                raise
            if rec['year'] == year:
                if len(rec['code'])!=6:
                    continue
                current_recs.append(rec)
                recs_by_code[rec['code']] = rec
            elif rec['year'] == year-1:
                for equiv in rec.get('equiv_code',[]):
                    if len(equiv) == 12:
                        prev_recs_by_code.setdefault(equiv,[]).append(rec)
        # print current_recs[:10]
        # print list(recs_by_code.iteritems())[:10]
        # print list(prev_recs_by_code.iteritems())[:10]
        out = []
        for rec in current_recs:
            equiv_code = "E%d/%s" % (rec['year'],rec['code'])
            equivs = prev_recs_by_code.get(equiv_code)
            if equivs is None:
                test_value = sum(rec.get(x,0)**2 for x in ['net_allocated','gross_allocated','commitment_allocated','net_used'])
                print "no equiv for %s, value=%d" % (rec['code'],test_value)
                continue
            erec = {'code': rec['code'],
                    'title': rec['title'] }
            for k,nk in [("net_allocated","orig"),("net_revised","rev")]:
                try:
                    erec["%s_%s" % (year,nk)] = rec[k]
                    erec["%s_%s" % (year-1,nk)] = sum(x[k] for x in equivs)
                    out.append(erec)
                except:
                    continue
        out = {'key':'budget-comparisons','value':out}
        file(outfile,'w').write(json.dumps(out,sort_keys=True))

if __name__=="__main__":
    prepare_compare_record().process(sys.argv[1],sys.argv[2],int(sys.argv[3]))
