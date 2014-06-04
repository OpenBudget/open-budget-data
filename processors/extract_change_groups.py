#encoding: utf8

import pystache
import json
import urllib2
import itertools
import pprint
import shelve
import math
import jinja2
import datetime
from numpy import array
from itertools import chain

if __name__ == "__main__":
    input = sys.argv[1]
    output = sys.argv[2]
    processor = extract_change_groups().process(input,output)

fields = ['net_expense_diff',
          'gross_expense_diff',
          'allocated_income_diff',
          'commitment_limit_diff',
          'personnel_max_diff']

def change_to_vec(change):
    return array([change[x] for x in fields])

def transfer_code(change):
    return "%d/%02d-%03d" % (change['year'],change['leading_item'],change['req_code'])

def powerset(iterable):
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(2,min(len(s)+1,6)))

def subsets(s):
    return map(set, powerset(s))

def combinations(iterable, r):
    # combinations('ABCD', 2) --> AB AC AD BC BD CD
    # combinations(range(4), 3) --> 012 013 023 123
    def get_next(next_of,i):
        ret = nexts.get(next_of,next_of+1)
        if ret > i + n - r:
            ret = i + n - r
        return ret

    pool = tuple(iterable)
    n = len(pool)
    if r > n:
        return
    nexts = dict(zip(range(n-1),range(1,n)))
    indices = range(r)
    yield tuple(pool[i] for i in indices)
    while True:
        for i in reversed(range(r)):
            if indices[i] != i + n - r:
                break
        else:
            return
        indices[i] = get_next(indices[i],i)
        for j in range(i+1, r):
            indices[j] = get_next(indices[j-1],j)
        found = (yield tuple(pool[i] for i in indices))
        if found:
            for i in indices:
                target = nexts.get(i)
                sources = (k for k,v in nexts.iteritems() if v==i)
                if target is not None:
                    for src in sources:
                        nexts[src] = target
                else:
                    for src in list(sources):
                        del nexts[src]
            indices[0] = get_next(indices[0],0)
            for j in range(1,r):
                indices[j] = get_next(indices[j-1],j)
            #print "nexts",len(set(nexts.values()))

def get_groups(changes):
    for change in changes:
        change['trcode'] = transfer_code(change)
        for k,v in change.iteritems():
            if k.startswith('date'):
                change['date'] = v
                change['date_kind'] = k[5:]+"/"+v
                break
        if change.get('date') is None:
            print change
    get_date = lambda x:x['date_kind']
    changes.sort(key=get_date)
    groups = []
    selected_transfer_codes = set()
    for date_kind, date_changes in itertools.groupby(changes, get_date):
        date_changes = list(date_changes)
        date = date_changes[0]['date']
        print 'reserve date:',date_kind
        date_reserve = [c for c in date_changes if c['budget_code'].startswith('0047')
                        if sum(c[field]*c[field] for field in fields) > 0]
        #print 'len(date_reserve)=',len(date_reserve)
        for comb_size in range(2,min(len(date_reserve),8)):
            done = False
            #print "comb_size", comb_size
            while not done:
                not_selected = list(x for x in date_reserve if x['trcode'] not in selected_transfer_codes)
                #print 'len(not_selected)=',len(not_selected)
                date_groups = combinations(not_selected,comb_size)
                found = None
                done = True
                try:
                    while True:
                        group = date_groups.send(found)
                        found = False
                        vecs = list(change_to_vec(c) for c in group)
                        sumvec = sum(vecs)
                        if len(sumvec)>1:
                            sumvec = sum(sumvec)
                        if sumvec == 0:
                            transfer_codes = set(x['trcode'] for x in group)
                            if len(selected_transfer_codes & transfer_codes) > 0:
                                continue
                            selected_transfer_codes.update(transfer_codes)
                            transfer_codes = list(transfer_codes)
                            transfer_codes.sort()
                            to_append = { 'transfer_ids': transfer_codes,
                                          'date': date}
                            print to_append
                            groups.append(to_append)
                            found = True
                except StopIteration:
                    pass
                #print "considered %d combinations" % i
    all_transfer_codes = set((x['trcode'],x['date']) for x in changes)
    for trcode,date in all_transfer_codes:
        if not trcode in selected_transfer_codes:
            groups.append({'transfer_ids': [trcode],
                            'date': date})
    for group in groups:
        trcodes = set(group['transfer_ids'])
        years = list(set(int(x.split('/')[0]) for x in trcodes))
        assert(len(years)==1)
        group['year'] = years[0]
        group['transfer_ids'] = list(set(x.split('/')[1] for x in trcodes))
        transfer_changes = list(filter(lambda x:x['trcode'] in trcodes,changes))
        #group['changes'] = transfer_changes
        group['budget_codes'] = list(set(x['budget_code'] for x in transfer_changes))
        group['prefixes'] = list(set(chain.from_iterable([code[:l] for l in range(2,8,2)] for code in group['budget_codes'])))
        group['group_id'] = group['transfer_ids'][0]

    return groups

class extract_change_groups(object):
    def process(self,input,output):
        changes = [json.loads(line.strip()) for line in file(input)]
        groups = get_groups(changes)
        out = file(output,'w')
        for group in groups:
            out.write(json.dumps(group,sort_keys=True)+'\n')
