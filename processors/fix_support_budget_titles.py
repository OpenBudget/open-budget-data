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
        supports2 = {}

        supports_jsons, budget_jsons = inputs

        for line in file(budget_jsons):
            line = json.loads(line.strip())
            budgets["%(year)s/%(code)s" % line] = line['title']
            # if line.get('title','') != '':
            #     budgets2.setdefault("%(year)s/%(title)s" % line,[]).append(line['code'])

        for line in file(supports_jsons):
            line = json.loads(line.strip())
            if line.get('title','') != '':
                if budgets.get("%(year)s/%(code)s" % line) is not None:
                    supports.setdefault("%(year)s/%(title)s" % line,set()).add(line['code'])
            if line.get('subject','') != '':
                if budgets.get("%(year)s/%(code)s" % line) is not None:
                    supports2.setdefault("%(year)s/%(subject)s" % line,set()).add(line['code'])

        errors = {}

        outfile = file(output,"w")
        changed_num = 0
        for line in file(supports_jsons):
            datum = json.loads(line.strip())
            year = datum['year']
            key_code = "%s/%s" % (year, datum['code'])
            title = budgets.get(key_code)
            if title is not None:
                # Code is valid, just fix title
                if title != datum.get('title',''):
                    datum['title'] = title
                    changed_num += 1
            else:
                key_title = "%s/%s" % (year, datum['title'])
                possible_codes = supports.get(key_title,[])
                if len(possible_codes) == 1:
                    # There's only one valid budget code for this support title
                    datum['code'] = possible_codes[0]
                    key_code = "%s/%s" % (year, datum['code'])
                    title = budgets.get(key_code)
                    if title is not None:
                        datum['title'] = title
                    changed_num += 1
                else:
                    key_subject = "%s/%s" % (year, datum['subject'])
                    possible_codes = supports2.get(key_subject,[])
                    if len(possible_codes) == 1:
                        # There's only one valid budget code for this support subject
                        datum['code'] = possible_codes[0]
                        key_code = "%s/%s" % (year, datum['code'])
                        title = budgets.get(key_code)
                        if title is not None:
                            datum['title'] = title
                        changed_num += 1
                    else:
                        errors.append((key_code,possible_codes))
            outfile.write(json.dumps(datum,sort_keys=True)+"\n")

        for error in errors.values():
            logging.error("Failed to find title for support with key %s: pc=%r" % error)

        logging.info("updated %d entries" % changed_num)
