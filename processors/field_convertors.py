#encoding: utf8
from datetime import date, datetime
import calendar
import re
import time

id = lambda x:x

integer = lambda x: int(x) if x is not None else None
boolean = lambda x: x.strip().lower() in ["true","1","yes"] if type(x) in [str,unicode] else x
newlines_to_br = lambda x: x.replace('\n','<br/>')
canonize_integer = lambda x: int(x.replace(",",""))
canonize_float = lambda x: float(x.replace(",",""))
comma_separated_list = lambda x: [xx.strip() for xx in x.split(",")]
nbsp = lambda x: x.replace(u'\u00a0', ' ')
c_code = lambda x: re.findall('[0-9]+',x)[0]
utf8_decoder = lambda x: x.decode('utf8')
win_decoder = lambda x: x.decode('cp1255')
reg_date = lambda x: time.mktime(datetime.strptime(x, "%Y-%m-%d %H:%M:%S").timetuple()) if x.strip() != '' else None
number = lambda x: canonize_float(x) if x is not None else None

def simple_date_from_spreadsheet(datestr):
    if datestr is None: return None
    d = datetime.strptime(datestr.strip(),"%d.%m.%Y").timetuple()
    return calendar.timegm(d)

def canonize_budget_code(code):
    code = str(code).replace("-","")
    if len(code) % 2 == 1:
        code = "0"+code
    code = "00"+code
    return code

def canonize_date(datestr):
    datestr = datestr.replace('ינו','1').replace('פבר','2').replace('מרץ','3').replace('אפר','4')\
                         .replace('מאי','5').replace('יונ','6').replace('יול','7').replace('אוג','8').replace('ספט','9')\
                         .replace('אוק','10').replace('נוב','11').replace('דצמ','12')
    datestr = datestr.replace('B1','').replace('Jan','1').replace('Feb','2').replace('Mar','3').replace('Apr','4')\
                       .replace('May','5').replace('Jun','6').replace('Jul','7').replace('Aug','8').replace('Sep','9')\
                       .replace('Oct','10').replace('Nov','11').replace('Dec','12')
    datestr = datestr.replace('B1','')
    if '-' in datestr:
        datestr = datestr.split('-')
        d = [ int(x) for x in datestr ]
        if d[2] < 100:
            d[2] += 2000
        datestr = "%s/%s/%s" % (d[0],d[1],d[2])
    elif "/" in datestr and int(datestr[-2:])<12:
        datestr = datestr.split('/')
        d = [ int(x) for x in datestr ]
        d[2] += 2000
        datestr = "%s/%s/%s" % (d[1],d[0],d[2])
    if datestr[-4:-2]=="20":
        out = datetime.strptime(datestr,"%d/%m/%Y").date()
    out = datetime.strftime(out,"%d/%m/%Y")
    return out

ngo_kind = lambda x:{u'חל"ץ':'cic',u'עמותה':'association'}[x.decode('utf8')]
