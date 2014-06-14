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
            budgets["%(year)s/%(code)s" % line] = line['title']

        outfile = file(output,"w")
        changed_num = 0
        for line in file(changes_jsons):
            line = json.loads(line.strip())
            year = line['year']
            if line.has_key('changes'):
                data = line['changes']
            else:
                data = [line]
            for datum in data:
                key = "%s/%s" % (year, datum['budget_code'])
                title = budgets.get(key)
                if title != None:
                    if title != line.get('budget_title',''):
                        datum['budget_title'] = title
                        changed_num += 1
                else:
                    logging.error("Failed to find title for change with key %s" % key)
            outfile.write(json.dumps(line,sort_keys=True)+"\n")
        print "updated %d entries" % changed_num
