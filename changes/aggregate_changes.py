#encoding: utf8
### שנה,סעיף מוביל,מספר בקשה,תיאור בקשה,קוד שינוי,שם שינוי,קוד סוג בקשה,שם סוג בקשה,מספר וועדה,קוד תוכנית,שם תוכנית,הוצאות נטו,הוצאה מותנית בהכנסה,הכנסה מיועדת,הרשאה להתחייב,שיא כא,תאריך אישור

import sys
import csv
import glob
import gzip

if __name__=="__main__":
    explanations = {}
    for row in csv.reader(file("../change_explanation/explanations.csv")):
        year,req_pri,req_sec,date,explanation = row
        key = "%s/%s/%s" % (year,req_pri,req_sec)
        explanations[key] = (date,explanation)

    def rows():
        for changes_file in glob.glob("*.csv"):
            for row in csv.reader(file(changes_file)):
                year, leading_item, req_code, req_title, change_code, change_title, change_type_id, change_type_name, committee_id, budget_code, budget_title, net_expense_diff, gross_expense_diff, allocated_income_diff, commitment_limit_diff, personnel_max_diff = row[:16]
                try:
                    year = int(year)
                except:
                    continue
                leading_item = int(leading_item)
                req_code = int(req_code)
                req_title = req_title
                change_code = int(change_code)
                change_title = change_title
                change_type_id = int(change_type_id)
                change_type_name = change_type_name
                committee_id = int(committee_id)
                budget_code = "00"+budget_code
                budget_title = budget_title
                net_expense_diff = int(net_expense_diff.replace(',',''))
                gross_expense_diff = int(gross_expense_diff.replace(',',''))
                allocated_income_diff = int(allocated_income_diff.replace(',',''))
                commitment_limit_diff = int(commitment_limit_diff.replace(',',''))
                personnel_max_diff = float(personnel_max_diff.replace(',',''))
                
                explanation_key = "%d/%d/%d" % (year,leading_item,req_code)
                date,explanation = explanations.get(explanation_key,(None,""))
                
                row = [ year, leading_item, req_code, req_title, change_code, change_title, change_type_id, change_type_name, committee_id, budget_code, budget_title, net_expense_diff, gross_expense_diff, allocated_income_diff, commitment_limit_diff, personnel_max_diff, date, explanation ]
                yield row

    csv.writer(gzip.GzipFile('changes_total.csv.gz','w')).writerows(rows())
