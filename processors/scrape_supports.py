#encoding: utf8

import gzip
import time
import requesocks as requests
import csv
import re
import subprocess
from pyquery import PyQuery as pq
]
codes = [
 ('2900',
  u'\u05de\u05e9\u05e8\u05d3 \u05d4\u05d1\u05d9\u05e0\u05d5\u05d9 \u05d5\u05d4\u05e9\u05d9\u05db\u05d5\u05df'),
 ('3600', u'\u05de\u05e9\u05e8\u05d3 \u05d4\u05ea\u05de\u05ea'),
 ('0400',
  u'\u05de\u05e9\u05e8\u05d3 \u05e8\u05d0\u05e9 \u05d4\u05de\u05de\u05e9\u05dc\u05d4'),
 ('5900',
  u'\u05e9\u05e8\u05d5\u05ea \u05d4\u05ea\u05e2\u05e1\u05d5\u05e7\u05d4'),
 ('3000',
  u'\u05d4\u05de\u05e9\u05e8\u05d3 \u05dc\u05e7\u05dc\u05d9\u05d8\u05ea \u05e2\u05dc\u05d9\u05d4'),
 ('1100',
  u'\u05de\u05e9\u05e8\u05d3 \u05d4\u05ea\u05d9\u05d9\u05e8\u05d5\u05ea'),
 ('2400',
  u'\u05de\u05e9\u05e8\u05d3 \u05d4\u05d1\u05e8\u05d9\u05d0\u05d5\u05ea'),
 ('3300',
  u'\u05de\u05e9\u05e8\u05d3 \u05d4\u05d7\u05e7\u05dc\u05d0\u05d5\u05ea \u05d5\u05e4\u05d9\u05ea\u05d5\u05d7 \u05d4\u05db\u05e4\u05e8'),
 ('0540',
  u'\u05de.\u05d4\u05d0\u05d5\u05e6\u05e8 - \u05de\u05d8\u05d4 \u05d4\u05d7\u05e9\u05d1 \u05d4\u05db\u05dc\u05dc\u05d9'),
 ('0490', u'\u05e8\u05d5\u05d4\u05de'),
 ('0000',
  u'\u05d0\u05e0\u05d0 \u05d1\u05d7\u05e8 \u05de\u05e9\u05e8\u05d3/\u05d9\u05d7\u05d9\u05d3\u05d4'),
 ('4050',
  u'\u05e8\u05e9\u05d5\u05ea \u05dc\u05d0\u05d5\u05de\u05d9\u05ea \u05dc\u05d1\u05d8\u05d9\u05d7\u05d5\u05ea \u05d3\u05e8\u05db\u05d9\u05dd'),
 ('5800',
  u'\u05d4\u05d0\u05d5\u05e6\u05e8-\u05d6\u05db\u05d5\u05d9\u05d5\u05ea \u05e0\u05d9\u05e6\u05d5\u05dc\u05d9 \u05d4\u05e9\u05d5\u05d0\u05d4'),
 ('5300', u'\u05dc\u05e9\u05db\u05ea \u05d4\u05e0\u05e9\u05d9\u05d0'),
 ('2200',
  u'\u05d4\u05de\u05e9\u05e8\u05d3 \u05dc\u05e9\u05d9\u05e8\u05d5\u05ea\u05d9 \u05d3\u05ea'),
 ('2000', u'\u05de\u05e9\u05e8\u05d3 \u05d4\u05d7\u05d9\u05e0\u05d5\u05da'),
 ('5200',
  u'\u05de\u05e9\u05e8\u05d3 \u05d4\u05de\u05d3\u05e2 \u05d5\u05d4\u05d8\u05db\u05e0\u05d5\u05dc\u05d5\u05d2\u05d9\u05d4'),
 ('2300', u'\u05de\u05e9\u05e8\u05d3 \u05d4\u05e8\u05d5\u05d5\u05d7\u05d4'),
 ('3600', u'\u05de\u05e9\u05e8\u05d3 \u05d4\u05db\u05dc\u05db\u05dc\u05d4'),
 ('1600',
  u'\u05d4\u05de\u05e9\u05e8\u05d3 \u05dc\u05d4\u05d2\u05e0\u05ea \u05d4\u05e1\u05d1\u05d9\u05d1\u05d4'),
 ('0600', u'\u05de\u05e9\u05e8\u05d3 \u05d4\u05e4\u05e0\u05d9\u05dd'),
 ('0420',
  u'\u05e4\u05d9\u05ea\u05d5\u05d7 \u05e0\u05d2\u05d1, \u05d2\u05dc\u05d9\u05dc \u05d5\u05e9.\u05e4\u05e2\u05d5\u05dc\u05d4'),
 ('2950', u'\u05ea\u05e0\u05d5\u05e4\u05d4'),
 ('5210',
  u'\u05de\u05e9\u05e8\u05d3 \u05d4\u05ea\u05e8\u05d1\u05d5\u05ea \u05d5\u05d4\u05e1\u05e4\u05d5\u05e8\u05d8'),
 ('5400',
  u'\u05d4\u05d7\u05d8\u05d9\u05d1\u05d4 \u05dc\u05d4\u05ea\u05d9\u05e9\u05d1\u05d5\u05ea'),
 ('1700',
  u'\u05ea\u05d9\u05d0\u05d5\u05dd \u05d4\u05e4\u05e2\u05d5\u05dc\u05d5\u05ea \u05d1\u05e9\u05d8\u05d7\u05d9\u05dd'),
 ('5700',
  u'\u05d4\u05de\u05e9\u05e8\u05d3 \u05dc\u05d1\u05d8\u05d7\u05d5\u05df \u05e4\u05e0\u05d9\u05dd'),
 ('0500', u'\u05de\u05e9\u05e8\u05d3 \u05d4\u05d0\u05d5\u05e6\u05e8'),
 ('4000',
  u'\u05de\u05e9\u05e8\u05d3 \u05d4\u05ea\u05d7\u05d1\u05d5\u05e8\u05d4'),
 ('1200',
  u'\u05de\u05e9\u05e8\u05d3 \u05d4\u05d0\u05e0\u05e8\u05d2\u05d9\u05d4 \u05d5\u05d4\u05de\u05d9\u05dd'),
 ('3700',
  u'\u05de.\u05d4\u05d0\u05d5\u05e6\u05e8 - \u05de\u05e0\u05d4\u05dc\u05ea \u05d4\u05d2\u05de\u05dc\u05d0\u05d5\u05ea'),
 ('5500', u'\u05e8\u05e9\u05d5\u05ea \u05d4\u05de\u05d9\u05dd'),
 ('3200',
  u'\u05de. \u05d4\u05d7\u05d9\u05e0\u05d5\u05da-\u05d7\u05d9\u05e0\u05d5\u05da \u05d4\u05ea\u05d9\u05d9\u05e9\u05d1\u05d5\u05ea\u05d9'),
 ('2080',
  u'\u05d7\u05d9\u05e0\u05d5\u05da-\u05d0\u05d2\u05e3 \u05dc\u05de\u05d5\u05e1\u05d3\u05d5\u05ea \u05ea\u05d5\u05e8\u05e0\u05d9\u05d9\u05dd'),
 ('5000',
  u'\u05de\u05e9\u05e8\u05d3 \u05d4\u05ea\u05e7\u05e9\u05d5\u05e8\u05ea')]

DataURL = "http://tmichot.gov.il/ibi_apps/WFServlet?IBIF_webapp=/ibi_apps&IBIC_server=EDASERVE&IBIF_ex=suppe_notif_item_all6&CLICKED_ON=&LSMYEAR=%(year)s&COMP_CODE=%(hcode)s&COMP_CODE_DISPLAY=%%E4%%EE%%F9%%F8%%E3%%20%%EC%%E4%%E2%%F0%%FA%%20%%E4%%F1%%E1%%E9%%E1%%E4&NOTTYPE_LIST=FOC_NONE&LSCOMMIT_LIST=%(code)s&MDRILL=1&YEARTXT=%(year)s1231"
CodesURL = "http://tmichot.gov.il/ibi_apps/WFServlet?IBIF_ex=runtrig&TRIGGER0=1&TRIGGER1=suppe_trg_lst_cc_commit&SW_CURROBJ=COMP_CODE&APPID=supp_ext_app&LSTFRMID=suppe_notif_item_all6&FRAMEPCT=0&DO_fex=suppe_notif_item_all6&SW_CLICKED=&LSMYEAR=%(year)s&COMP_CODE=%(hcode)s&NOTTYPE_LIST=FOC_NONE&NOTTYPE=FOC_NONE&LSMCOMMITXT=&LSCOMMIT_LIST=FOC_NONE&LSCOMMIT=FOC_NONE&OUTPUT=HTML&LSMYEAR_DISPLAY=%(year)s&COMP_CODE_DISPLAY=%%E4%%EE%%F9%%F8%%E3+%%EC%%E1%%E8%%E7%%E5%%EF+%%F4%%F0%%E9%%ED&NOTTYPE_DISPLAY=%%E4%%EB%%EC&LSCOMMIT_DISPLAY=%%E4%%EB%%EC&OUTPUT_DISPLAY=%%E4%%F6%%E2%%FA+%%E3%%E5%%E7&SW_INITIAL=N&RAND=0.9564581164158881"
CodesRE = re.compile('set1\("([0-9]+)',re.M)

class scrape_supports(object):

    def process(self,input,output,year,PROXY=None):
        session = requests.session()
        if PROXY is not None:
            session.proxies = {'http': 'socks5://'+PROXY}

        out = csv.writer(file(output,"w"))
        for hcode, title in codes:

            fmt = {'year':year,'hcode':hcode }

            item_codes = session.get(CodesURL % fmt).text
            item_codes = CodesRE.findall(item_codes)
            print item_codes

            for item_code in item_codes:
                fmt['code'] = item_code

                url = "http://obudget.org/api/supports/00{0}/{1}?limit=5000".format(item_code,year)
                rows = requests.get(url).json()
                rows = [ [ str(y).encode('utf8') for y  in [x['year'], '', x['subject'], item_code,
                                                            x['recipient'], x['kind'],
                                                            x['title'], 0, 0, 0]] for x in rows ]
                out.writerows(rows)

                print year,hcode,title.encode('utf8'),item_code

                for i in range(10):
                    try:
                       frame = session.get(DataURL % fmt).text
                       break
                    except:
                       time.sleep(60)
                       pass
                frame = pq(frame)
                for row in frame("TR"):
                    row = pq(row)
                    _row = [year,hcode,title.encode('utf8'),item_code]
                    for x in row("TD.x3_0, TD.x3_1, TD.x2_0, TD.x2_1"):
                        x=pq(x)
                        x=x.text()
                        try:
                            _row.append(int(x.replace(",","")))
                        except:
                            _row.append(x.encode('utf8'))
                    if len(_row) > 4:
                        out.writerow(_row)
                        print _row
