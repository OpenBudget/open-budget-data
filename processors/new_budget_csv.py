#encoding: utf8

import csv
import json
import logging
import sys

ROOT_COL = None
def indexof(*args):
    row = args[0]
    names = args[1:]
    for name in names:
        for i,_h in enumerate(row):
            h = _h.decode('utf8')
            if all(word in h for word in name.split()):
                return i
    logging.error('cant find %s in row!' % "/".join(names))
    logging.error('row=%s' % ", ".join(row))
    return None

def to_code(row,col):
    t = row[col]
    if '-' in t:
        t = t.split('-')
        assert(len(t)==((col-ROOT_COL+2)/2))
        t= [ "%02d" % int(x) for x in t ]
        t = "00" + ''.join(t)
    else:
        add = "0" * (col-ROOT_COL+4-len(t))
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

def add_to_list(key,sums,item,field):
    if item is not None:
        if item not in sums[key][field]:
            sums[key][field].append(item)
    if len(sums[key][field])>1 and len(key)>=11:
        logging.error("TOO MANY GROUPS FOR %r" % sums[key])

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
                global ROOT_COL
                ROOT_COL = SAIF_COL
                SAIF_NAME_COL = indexof(row,u'שם סעיף')
                THUM_COL = indexof(row,u'קוד תחום')
                THUM_NAME_COL = indexof(row,u'שם תחום')
                PROG_COL = indexof(row,u'קוד תוכנית')
                PROG_NAME_COL = indexof(row,u'שם תוכנית')
                TAKA_COL = indexof(row,u'קוד תקנה')
                TAKA_NAME_COL = indexof(row,u'שם תקנה מלא',u'שם תקנה')

                NET_ALLOC_COL = indexof(row,u'מקורי נטו')
                GROSS_ALLOC_COL = indexof(row,u'מקורי הוצאה מותנית')

                DEDICATED_ALLOC_COL = indexof(row,u'מקורי הכנסה מיועדת')
                COMMITMENT_ALLOC_COL = indexof(row,u'מקורי הרשאה')
                PERSONNEL_ALLOC_COL = indexof(row,u'מקורי שיא כא')
                CONTRACTORS_ALLOC_COL = indexof(row,u'מקורי עבצ')
                AMOUNTS_ALLOC_COL = indexof(row,u'מקורי כמויות')

                NET_REVISED_COL = indexof(row,u'מאושר נטו')
                GROSS_REVISED_COL = indexof(row,u'תקציב מאושר הוצאה מותנית בהכנסה')

                DEDICATED_REVISED_COL = indexof(row,u'מאושר הכנסה מיועדת')
                COMMITMENT_REVISED_COL = indexof(row,u'מאושר הרשאה')
                PERSONNEL_REVISED_COL = indexof(row,u'מאושר שיא כא')
                CONTRACTORS_REVISED_COL = indexof(row,u'מאושר עבצ')
                AMOUNTS_REVISED_COL = indexof(row,u'מאושר כמויות')

                USED_COL = indexof(row,u'ביצוע מזומן')

                ACTIVE_COL = indexof(row,u'תקנה פעילה')

                GROUP1_COL = indexof(row,u'שם רמה 1')
                GROUP2_COL = indexof(row,u'שם רמה 2')


                continue
            for col,title_col in [(SAIF_COL,SAIF_NAME_COL),(THUM_COL,THUM_NAME_COL),(PROG_COL,PROG_NAME_COL),(TAKA_COL,TAKA_NAME_COL)]:
                if col is None or title_col is None:
                    continue
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

                dedicated_allocated = get_from(row,DEDICATED_ALLOC_COL)
                commitment_allocated = get_from(row,COMMITMENT_ALLOC_COL)
                personnel_allocated = get_from(row,PERSONNEL_ALLOC_COL)
                contractors_allocated = get_from(row,CONTRACTORS_ALLOC_COL)
                amounts_allocated = get_from(row,AMOUNTS_ALLOC_COL)

                dedicated_revised = get_from(row,DEDICATED_REVISED_COL)
                commitment_revised = get_from(row,COMMITMENT_REVISED_COL)
                personnel_revised = get_from(row,PERSONNEL_REVISED_COL)
                contractors_revised = get_from(row,CONTRACTORS_REVISED_COL)
                amounts_revised = get_from(row,AMOUNTS_REVISED_COL)

                active = row[ACTIVE_COL].decode('utf8') != u'פש"ח'
                all_values = [net_allocated,gross_allocated,gross_allocated,gross_revised,net_used,dedicated_allocated,commitment_allocated,personnel_allocated,contractors_allocated,amounts_allocated,dedicated_revised,commitment_revised,personnel_revised,contractors_revised,amounts_revised]
                all_zeros = sum(abs(x) for x in all_values if x is not None) == 0
                if all_zeros and not active and year not in new_years:
                    continue

                group1 = group2 = None
                if GROUP1_COL is not None and GROUP2_COL is not None:
                    group1 = row[GROUP1_COL].decode('utf8')
                    group2 = row[GROUP2_COL].decode('utf8')
                group_top = group1
                group_full = group2

                key = "%s/%s" % (year,code)
                sums.setdefault(key,{'code':code,'year':year,'title':title,'group_top':[], 'group_full':[]})
                add_to_sums(key,sums,net_allocated,'net_allocated')
                add_to_sums(key,sums,net_revised,'net_revised')
                add_to_sums(key,sums,net_used,'net_used')
                add_to_sums(key,sums,gross_allocated,'gross_allocated')
                add_to_sums(key,sums,gross_revised,'gross_revised')

                add_to_sums(key,sums,dedicated_allocated,'dedicated_allocated')
                add_to_sums(key,sums,commitment_allocated,'commitment_allocated')
                add_to_sums(key,sums,personnel_allocated,'personnel_allocated')
                add_to_sums(key,sums,contractors_allocated,'contractors_allocated')
                add_to_sums(key,sums,amounts_allocated,'amounts_allocated')

                add_to_sums(key,sums,dedicated_revised,'dedicated_revised')
                add_to_sums(key,sums,commitment_revised,'commitment_revised')
                add_to_sums(key,sums,personnel_revised,'personnel_revised')
                add_to_sums(key,sums,contractors_revised,'contractors_revised')
                add_to_sums(key,sums,amounts_revised,'amounts_revised')

                add_to_list(key,sums,group_top,'group_top')
                add_to_list(key,sums,group_full,'group_full')

        keys = sums.keys()
        keys.sort()

        out = file(output,"w")
        for key in keys:
            out.write("%s\n" % json.dumps(sums[key]))

if __name__ == "__main__":
    input = sys.argv[1]
    output = sys.argv[-1]
    processor = new_budget_csv().process(input,output,[2014,2015])
