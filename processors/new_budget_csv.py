#encoding: utf8

import csv
import json
import logging

if __name__ == "__main__":
    inputs = sys.argv[1:-1]
    output = sys.argv[-1]
    processor = new_budget_csv().process(inputs,output)

def indexof(*args):
    row = args[0]
    names = args[1:]
    for name in names:
        for i,h in enumerate(row):
            if name in h.decode('utf8'):
                return i
    logging.error('cant find %s in row!' % "/".join(names))
    logging.error('row=%s' % ", ".join(row))
    return None

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
        if index is None:
            return None
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

    def process(self,input,output,new_years=[]):
        sums = {}
        budgets=csv.reader(file(input))
        YEAR_COL = None
        for row in budgets:
            try:
                year = int(row[YEAR_COL])
            except:
                if YEAR_COL is not None:
                    continue
                YEAR_COL = indexof(row,u'שנה')
                SAIF_COL = indexof(row,u'קוד סעיף')
                SAIF_NAME_COL = indexof(row,u'שם סעיף')
                THUM_COL = indexof(row,u'קוד תחום')
                THUM_NAME_COL = indexof(row,u'שם תחום')
                PROG_COL = indexof(row,u'קוד תוכנית')
                PROG_NAME_COL = indexof(row,u'שם תוכנית')
                TAKA_COL = indexof(row,u'קוד תקנה')
                TAKA_NAME_COL = indexof(row,u'שם תקנה מלא',u'שם תקנה')
                NET_ALLOC_COL = indexof(row,u'מקורי - נטו',u'מקורי - הוצאות נטו')
                GROSS_ALLOC_COL = indexof(row,u'מקורי - הוצאה מותנית')
                NET_REVISED_COL = indexof(row,u'מאושר - הוצאות נטו')
                GROSS_REVISED_COL = indexof(row,u'תקציב מאושר - הוצאה מותנית בהכנסה')
                USED_COL = indexof(row,u'ביצוע - מזומן')
                continue
            for col,title_col in [(SAIF_COL,SAIF_NAME_COL),(THUM_COL,THUM_NAME_COL),(PROG_COL,PROG_NAME_COL),(TAKA_COL,TAKA_NAME_COL)]:
                code = to_code(row,col)
                # if len(code) != col+3:
                #     logging.error("%s, %s" % (code, row))
                #     assert(False)
                new_year = year in new_years and len(code) < 10
                title = row[title_col].decode('utf8')
                net_allocated = get_from(row,NET_ALLOC_COL)
                gross_allocated = get_from(row,GROSS_ALLOC_COL,net_allocated)
                net_revised = get_from(row,NET_REVISED_COL) if not new_year else net_allocated
                gross_revised = get_from(row,GROSS_REVISED_COL,net_revised) if not new_year else gross_allocated
                net_used = get_from(row,USED_COL)

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
