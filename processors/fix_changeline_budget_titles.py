import json
import logging

if __name__ == "__main__":
    input = sys.argv[1]
    output = sys.argv[2]
    processor = fix_changeline_budget_titles().process(input,output,[])

class fix_changeline_budget_titles(object):

    def process(self,inputs,output):

        out = []

        budgets = {}

        changes_jsons, budget_jsons = inputs

        for line in file(budget_jsons):
            line = json.loads(line.strip())
            budgets["%(year)s/%(code)s" % line] = (line['title'],line.get('equiv_code'))

        outfile = file(output,"w")
        changed_num = 0
        for line in file(changes_jsons):
            line = json.loads(line.strip())
            year = line['year']
            changegroup = False
            if line.has_key('changes'):
                changegroup = True
                data = line['changes']
            else:
                data = [line]
            for datum in data:
                key = "%s/%s" % (year, datum['budget_code'])
                title, equiv_code = budgets.get(key)
                if title != None:
                    changed = False
                    if equiv_code is not None:
                        datum['equiv_code'] = equiv_code
                        changed = True
                    if title != line.get('budget_title',''):
                        datum['budget_title'] = title
                        changed = True
                    if changed:
                        changed_num += 1
                else:
                    logging.error("Failed to find title for change with key %s" % key)
            if changegroup:
                group = line
                if len(group['transfer_ids']) == 1:
                    change = [ch for ch in group['changes'] if ch['budget_code']=="0047"]
                    if len(change)==0:
                        #logging.warn("can't find template for %r/%d" % (group['transfer_ids'],group['year']))
                        changes = [ch for ch in group['changes'] if len(ch['budget_code'])==4 and ch['budget_code']!="0047"]
                        change = {}
                        change['expense_change'] = -sum(x['expense_change'] for x in changes)
                        change['commitment_change'] = -sum(x['commitment_change'] for x in changes)
                        change['personnel_change'] = -sum(x['personnel_change'] for x in changes)
                    else:
                        change = change[0]
                    if change['expense_change'] < 0:
                        template = 'enlargement-expense'
                        value = -change['expense_change']
                    elif change['expense_change'] > 0:
                        template = 'cutbacks-expense'
                        value = change['expense_change']
                    elif change['commitment_change'] < 0:
                        template = 'allocation-commitment'
                        value = -change['commitment_change']
                    elif change['commitment_change'] > 0:
                        template = 'cutbacks-commitment'
                        value = change['commitment_change']
                    elif change['personnel_change'] < 0:
                        template = 'allocation-personnel'
                        value = int(-change['personnel_change'])
                    elif change['personnel_change'] > 0:
                        template = 'cutbacks-personnel'
                        value = int(change['personnel_change'])
                    else:
                        template = 'internal-change'
                        changes = [ch for ch in group['changes'] if len(ch['budget_code'])==4 and ch['budget_code']!="0047"]
                        if len(changes) > 0:
                            value = max(abs(c['expense_change']) for c in changes)
                        else:
                            value = 0

                    group['title_template'] = template
                    group['title_value'] = value
                    group['titles'] = [ch['budget_title'] for ch in group['changes'] if len(ch['budget_code'])==4 and ch['budget_code']!="0047"]
                else:
                    changes = [ch for ch in group['changes'] if len(ch['budget_code'])==4 and ch['budget_code']!="0047"]
                    def is_allocation(change):
                        if change['expense_change'] == 0:
                            if change['commitment_change'] == 0:
                                if change['personnel_change'] == 0:
                                    return True
                                else:
                                    return change['personnel_change'] > 0
                            else:
                                return change['commitment_change'] > 0
                        else:
                            return change['expense_change'] > 0
                    minus_transfers = filter(lambda x:not is_allocation(x),changes)
                    plus_transfers = filter(lambda x:is_allocation(x),changes)
                    value = sum(x['expense_change'] for x in plus_transfers)
                    if value == 0:
                        value = sum(x['commitment_change'] for x in plus_transfers)
                        if value == 0:
                            value = int(sum(x['personnel_change'] for x in plus_transfers))
                            if value == 0:
                                template = 'transfer-generic'
                            else:
                                template = 'transfer-personnel'
                        else:
                            template = 'transfer-commitment'
                    else:
                        template = 'transfer-expenses'
                    group['title_template'] = template
                    group['title_value'] = value
                    title = lambda x:x['budget_title']
                    group['titles'] = [map(title,minus_transfers),map(title,plus_transfers)]

                group['changes'].sort(key=lambda x: int("1"+x['budget_code']))

            outfile.write(json.dumps(line,sort_keys=True)+"\n")
        logging.info("updated %d entries" % changed_num)
