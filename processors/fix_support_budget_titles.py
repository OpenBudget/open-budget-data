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
        budgets2 = {}
        supports = {}

        supports_jsons, budget_jsons = inputs

        for line in file(budget_jsons):
            line = json.loads(line.strip())
            budgets["%(year)s/%(code)s" % line] = line['title']
            budgets2.setdefault("%(year)s/%(title)s" % line,[]).append(line['code'])

        for line in file(supports_jsons):
            line = json.loads(line.strip())
            supports.setdefault("%(year)s/%(title)s" % line,[]).append(line['code'])

        errors = {}

        outfile = file(output,"w")
        changed_num = 0
        for line in file(supports_jsons):
            datum = json.loads(line.strip())
            year = datum['year']
            key_code = "%s/%s" % (year, datum['code'])
            title = budgets.get(key_code)
            if title != None:
                if title != datum.get('title',''):
                    datum['title'] = title
                    changed_num += 1
            else:
                key_title = "%s/%s" % (year, datum['title'])
                possible_codes = budgets2.get(key_title,[])
                if len(possible_codes) == 1:
                    datum['code'] = possible_codes[0]
                    changed_num += 1
                else:
                    all_codes_for_title = supports.get(key_title,[])
                    all_valid_codes = [ x for x in all_codes_for_title if "%s/%s" % (year,x) in budgets ]
                    if len(all_valid_codes) == 1:
                        code = all_valid_codes[0]
                        datum['code'] = code
                        datum['title'] = budgets[ "%s/%s" % (year,code) ]
                        changed_num += 1
                    else:
                        errors[key_code] = (key_code, possible_codes, all_codes_for_title, all_valid_codes)
            outfile.write(json.dumps(datum,sort_keys=True)+"\n")

        for error in errors.values():
            logging.error("Failed to find title for support with key %s: pv=%r, ac=%r, vc=%r" % error)

        logging.info("updated %d entries" % changed_num)
