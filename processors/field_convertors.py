from datetime import date, datetime

id = lambda x:x

integer = lambda x: int(x)
canonize_integer = lambda x: int(x.replace(",",""))

canonize_float = lambda x: float(x.replace(",",""))

def canonize_budget_code(code):
    code = str(code).replace("-","")
    if len(code) % 2 == 1:
        code = "0"+code
    code = "00"+code
    return code

def canonize_date(datestr):
    if datestr.startswith("B1"):
        datestr = datestr.replace('B1','').replace('Jan','1').replace('Feb','2').replace('Mar','3').replace('Apr','4')\
                   .replace('May','5').replace('Jun','6').replace('Jul','7').replace('Aug','8').replace('Sep','9')\
                   .replace('Oct','10').replace('Nov','11').replace('Dec','12').split('-')
        d = [ int(x) for x in datestr ]
        if d[2] < 100:
            d[2] += 2000
        datestr = "%s/%s/%s" % (d[0],d[1],d[2])
    if datestr[-4:-2]=="20":
        out = datetime.strptime(datestr,"%d/%m/%Y").date()
    out = datetime.strftime(out,"%d/%m/%Y")
    return out
