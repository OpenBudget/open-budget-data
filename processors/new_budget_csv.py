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
            if name in h:
                return i
    logging.error('cant find %s in row!' % "/".join(names))
    logging.error('row=%s' % ", ".join(row))
    return None

def to_code(row,col):
    t = row[col]
    if len(t)==0:
        print "GOT EMPTY CODE! %s" % " ; ".join(x.decode('utf8') for x in row)
        return None
    if '-' in t:
        t = t.split('-')
        assert(len(t)==((col-ROOT_COL+3)/3))
        t= [ "%02d" % int(x) for x in t ]
        t = "00" + ''.join(t)
    else:
        add = "0" * (((col-ROOT_COL)/3)*2+4-len(t))
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
    # if len(sums[key][field])>1 and len(key)>=11 and field.startswith('group'):
    #     logging.error("TOO MANY GROUPS FOR %s %s: %r" % (field,key,sums[key]))

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
                PROG_COL = indexof(row,u'קוד תוכנית',u'קוד תכנית')
                PROG_NAME_COL = indexof(row,u'שם תוכנית',u'שם תכנית')
                TAKA_COL = indexof(row,u'קוד תקנה')
                TAKA_NAME_COL = indexof(row,u'שם תקנה מלא',u'שם תקנה')

                # NET_ALLOC_COL = indexof(row,u'מקורי נטו')
                # GROSS_ALLOC_COL = indexof(row,u'מקורי הוצאה מותנית')
                #
                # DEDICATED_ALLOC_COL = indexof(row,u'מקורי הכנסה מיועדת')
                # COMMITMENT_ALLOC_COL = indexof(row,u'מקורי הרשאה')
                # PERSONNEL_ALLOC_COL = indexof(row,u'מקורי שיא כא')
                # CONTRACTORS_ALLOC_COL = indexof(row,u'מקורי עבצ')
                # AMOUNTS_ALLOC_COL = indexof(row,u'מקורי כמויות')

                NET_COL = indexof(row,u'הוצאה נטו')
                GROSS_COL = indexof(row,u'הוצאה מותנית בהכנסה')

                DEDICATED_COL = indexof(row,u'הכנסה מיועדת')
                COMMITMENT_COL = indexof(row,u'הרשאה')
                PERSONNEL_COL = indexof(row,u'שיא כא',u'שיא כח אדם')
                CONTRACTORS_COL = indexof(row,u'עבצ')
                AMOUNTS_COL = indexof(row,u'כמויות',u'כמות')

                #USED_COL = indexof(row,u'ביצוע מזומן')

                ACTIVE_COL = indexof(row,u'תקנה פעילה')
                ONETIME_COL = indexof(row,u'פשח')

                INOUT_COL = indexof(row,u'סוג הוצאה',u'הוצאה/הכנסה')

                GROUP1_COL = indexof(row,u'שם רמה 1')
                GROUP2_COL = indexof(row,u'שם רמה 2')

                CLASS1_COL = indexof(row,u'שם מיון רמה 1')
                CLASS2_COL = indexof(row,u'שם מיון רמה 2')

                SUBKIND_COL = indexof(row,u'שם סוג סעיף')

                PHASE_COL = indexof(row,u'סוג תקציב')

                continue
            for col,title_col in [(SAIF_COL,SAIF_NAME_COL),(THUM_COL,THUM_NAME_COL),(PROG_COL,PROG_NAME_COL),(TAKA_COL,TAKA_NAME_COL)]:
                if col is None or title_col is None:
                    continue
                code = to_code(row,col)
                if code is None:
                    break
                # if len(code) != col+3:
                #     logging.error("%s, %s" % (code, row))
                #     assert(False)
                new_year = year in new_years and len(code) < 10
                title = row[title_col].decode('utf8')

                net = get_from(row,NET_COL)
                gross = get_from(row,GROSS_COL,net)
                dedicated = get_from(row,DEDICATED_COL)
                commitment = get_from(row,COMMITMENT_COL)
                personnel = get_from(row,PERSONNEL_COL)
                contractors = get_from(row,CONTRACTORS_COL)
                amounts = get_from(row,AMOUNTS_COL)

                if PHASE_COL is None:
                    continue
                phase = row[PHASE_COL].decode('utf8')
                if phase not in [u'מקורי',u'ביצוע',u'מאושר']:
                    continue

                if ACTIVE_COL is not None:
                    active = row[ACTIVE_COL].decode('utf8') != u'פש"ח'
                else:
                    active = True
                if ONETIME_COL is not None:
                    active = row[ONETIME_COL].decode('utf8') != u'1'
                else:
                    active = True

                tak_kind = 'unknown'
                if INOUT_COL is not None:
                    if row[INOUT_COL].decode('utf8') == u'הכנסה':
                        tak_kind = 'income'
                    elif row[INOUT_COL].decode('utf8') == u'הוצאה':
                        tak_kind = 'expense'

                tak_subkind = 'unknown'
                if SUBKIND_COL is not None:
                    tak_subkind = get_from(row,SUBKIND_COL)

                # all_values = [net_allocated,gross_allocated,gross_allocated,gross_revised,net_used,dedicated_allocated,commitment_allocated,personnel_allocated,contractors_allocated,amounts_allocated,dedicated_revised,commitment_revised,personnel_revised,contractors_revised,amounts_revised]
                # all_zeros = sum(abs(x) for x in all_values if x is not None) == 0
                # if all_zeros and not active and year not in new_years:
                #     continue

                group1 = group2 = None
                if GROUP1_COL is not None and GROUP2_COL is not None:
                    group1 = row[GROUP1_COL].decode('utf8')
                    group2 = row[GROUP2_COL].decode('utf8')
                group_top = group1
                group_full = group2

                class1 = class2 = None
                if CLASS1_COL is not None and CLASS2_COL is not None:
                    class1 = row[CLASS1_COL].decode('utf8')
                    class2 = row[CLASS2_COL].decode('utf8')
                class_top = class1
                class_full = class2

                key = "%s/%s" % (year,code)
                sums.setdefault(key,
                    {'code':code,
                     'year':year,
                     'title':title,
                     'group_top':[],
                     'group_full':[],
                     'class_top':[],
                     'class_full':[],
                     'kind':[],
                     'subkind':[]})

                if phase == u'מקורי':
                    add_to_sums(key,sums,net, 'net_allocated')
                    add_to_sums(key,sums,gross, 'gross_allocated')
                    add_to_sums(key,sums,dedicated, 'dedicated_allocated')
                    add_to_sums(key,sums,commitment, 'commitment_allocated')
                    add_to_sums(key,sums,personnel, 'personnel_allocated')
                    add_to_sums(key,sums,contractors, 'contractors_allocated')
                    add_to_sums(key,sums,amounts, 'amounts_allocated')

                    if new_year:
                        add_to_sums(key,sums,net, 'net_revised')
                        add_to_sums(key,sums,gross, 'gross_revised')
                        add_to_sums(key,sums,dedicated, 'dedicated_revised')
                        add_to_sums(key,sums,commitment, 'commitment_revised')
                        add_to_sums(key,sums,personnel, 'personnel_revised')
                        add_to_sums(key,sums,contractors, 'contractors_revised')
                        add_to_sums(key,sums,amounts, 'amounts_revised')

                    add_to_list(key,sums,group_top,'group_top')
                    add_to_list(key,sums,group_full,'group_full')
                    add_to_list(key,sums,class_top,'class_top')
                    add_to_list(key,sums,class_full,'class_full')

                    add_to_list(key,sums,tak_kind,'kind')
                    add_to_list(key,sums,tak_subkind,'subkind')

                elif phase == u'מאושר':
                    assert(not new_year)
                    add_to_sums(key,sums,net, 'net_revised')
                    add_to_sums(key,sums,gross, 'gross_revised')
                    add_to_sums(key,sums,dedicated, 'dedicated_revised')
                    add_to_sums(key,sums,commitment, 'commitment_revised')
                    add_to_sums(key,sums,personnel, 'personnel_revised')
                    add_to_sums(key,sums,contractors, 'contractors_revised')
                    add_to_sums(key,sums,amounts, 'amounts_revised')

                elif phase == u'ביצוע':
                    add_to_sums(key,sums,net,'net_used')


        keys = sums.keys()
        keys.sort()

        out = file(output,"w")
        for key in keys:
            out.write("%s\n" % json.dumps(sums[key]))

if __name__ == "__main__":
    input = sys.argv[1]
    output = sys.argv[-1]
    processor = new_budget_csv().process(input,output,[2015,2016])
