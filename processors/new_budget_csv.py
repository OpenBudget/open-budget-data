import csv
import json

if __name__ == "__main__":
    inputs = sys.argv[1:-1]
    output = sys.argv[-1]
    processor = new_budget_csv().process(inputs,output)

def to_code(row,col):
    t = row[col]
    if '-' in t:
        t = t.split('-')
        assert(len(t)==(col+1)/2)
        t= [ "%02d" % int(x) for x in t ]
        t = "00" + ''.join(t)
    else:
        add = "0" * (col+3-len(t))
        t=add+t
    return t

def get_from(row,index,to_add=0):
    try:
        val = row[index]
        val = val.replace(",","")
        if "." in val:
            return float(val)+to_add
        else:
            return int(val)+to_add
    except:
        return None

def add_to_sums(key,sums,amount,field):
    if amount is not None: sums[key][field] = sums[key].setdefault(field,0)+amount

class new_budget_csv(object):

    def process(self,input,output):
        sums = {}
        budgets=csv.reader(file(input))
        for row in budgets:
            try:
                year = int(row[0])
            except:
                continue
            for col in [1,3,5,7]:
                code = to_code(row,col)
                if len(code) != col+3:
                    print code, row
                    assert(False)
                title = row[col+1].decode('utf8')
                net_allocated = get_from(row,11)
                gross_allocated = get_from(row,12,net_allocated)
                net_revised = get_from(row,18)
                gross_revised = get_from(row,19,net_revised)
                net_used = get_from(row,25)

                key = "%s/%s" % (year,code)
                sums.setdefault(key,{'code':code,'year':year,'title':title})
                add_to_sums(key,sums,net_allocated,'net_allocated')
                add_to_sums(key,sums,net_revised,'net_revised')
                add_to_sums(key,sums,net_used,'net_used')
                add_to_sums(key,sums,gross_allocated,'gross_allocated')
                add_to_sums(key,sums,gross_revised,'gross_revised')

        keys = sums.keys()
        keys.sort()

        out = file(output,"w")
        for key in keys:
            out.write("%s\n" % json.dumps(sums[key]))
