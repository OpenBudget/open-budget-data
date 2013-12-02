import urllib2
import json
import re
import Levenshtein
from pyquery import PyQuery as pq

SEARCH_URL = "http://www.guidestar.org.il/search?search=%(query)s&op=%%D7%%97%%D7%%99%%D7%%A4%%D7%%95%%D7%%A9&form_id=guidestar_search_form"
ORG_URL_RE = re.compile("http://www\.guidestar\.org\.il/organization/[0-9]+")

def get_guidestar(name):
    parts = name.encode('utf8').split()
    href = None
    for i in range(len(parts),len(parts)-3,-1):
        query = " ".join(parts[0:i])
        if query == "": break
        url = SEARCH_URL % {'query':query}
        for _ in range(5):
            try:
                search = urllib2.urlopen(url).read()
                break
            except:
                time.sleep(1)
        search = pq(search)
        for result in search(".views-field-title-1 a"):
            result = pq(result)
            _href =result.attr("href")
            if Levenshtein.ratio(name,result.text()) > 0.5:
                href = _href
                break
        if href != None: break
    if not href: return None
    orginfo = None
    url = href
    for _ in range(5):
        try:
            orginfo = urllib2.urlopen(url).read()
            break
        except:
            time.sleep(1)
    ret = {'url':href}
    if orginfo != None:
        orginfo = pq(orginfo.decode('utf8'))
        ret['address'] = pq(orginfo(".views-field-nothing-1 .field-content")[0]).text()
        ret['objective'] = pq(orginfo(".views-field-field-gov-objectives .field-content")[0]).text()
    return ret
        
