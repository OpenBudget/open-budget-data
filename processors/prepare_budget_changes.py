import json

if __name__ == "__main__":
    input = sys.argv[1]
    output = sys.argv[2]
    processor = prepare_budget_changes().process(input,output,[])

class prepare_budget_changes(object):

    def process(self,input,output,new_years):

        out = []

        for line in file(input):
            line = line.strip()
            data = json.loads(line)
            year = data['year']
            if year not in new_years:
                continue
            for l in range(2,10,2):
                rec = {
                    'year': year,
                    'code': data['budget_code'][:l],
                    'net_revised': data['net_expense_diff'],
                    'gross_revised': data['net_expense_diff']+data['gross_expense_diff']
                }
                out.append(rec)

        outfile = file(output,"w")
        for rec in out:
            outfile.write(json.dumps(rec,sort_keys=True)+"\n")
