import json
import logging

if __name__ == "__main__":
    input = sys.argv[1]
    output = sys.argv[2]
    processor = fix_changeline_budget_titles().process(input,output,[])

class fix_support_budget_titles(object):

    def process(self,inputs,output):

        out = []

        budgets = {}

        supports_jsons, budget_jsons = inputs

        for line in file(budget_jsons):
            line = json.loads(line.strip())
            budgets["%(year)s/%(code)s" % line] = line['title']

        outfile = file(output,"w")
        changed_num = 0
        for line in file(supports_jsons):
            line = json.loads(line.strip())
            year = line['year']
            data = [line]
            for datum in data:
                key = "%s/%s" % (year, datum['code'])
                title = budgets.get(key)
                if title != None:
                    if title != line.get('title',''):
                        datum['title'] = title
                        changed_num += 1
                else:
                    logging.error("Failed to find title for change with key %s" % key)

            outfile.write(json.dumps(line,sort_keys=True)+"\n")
        logging.info("updated %d entries" % changed_num)
