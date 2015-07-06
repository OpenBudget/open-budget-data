#encoding: utf8
import json
import pyquery
from selenium import webdriver
import sys
import time

# path_to_phantomjs = "/usr/bin/phantomjs"
moital_contractors_url = (
    'http://apps.moital.gov.il/WebServicesHandlers/ServiceContractors.aspx')

header_conv = {
   u"כתובת" : "address",
   u"מס' רשיון" : "license_number",
   u"שם החברה" : "company_name",
   u"מנכ\"ל החברה" : "company_ceo",
   u"יישוב" : "locality",
   u"בעל החברה" : "owner",
   u"גמר תוקף" : "end_date",
   u"סטאטוס רישיון" : "license_status",
   u"ח.פ/ע.מ" : "company_id",
   u"תחום פעילות" : "field_of_activity"
}

def match_int(s, i):
    try:
        return int(s) == i
    except ValueError:
        return False

# Return a list of dicts containing rows.
def ParseOnePage(x):
    l = []
    # Table header. Will use these headings as keys to the records from all trs.
    th = [e.text_content() for e in x('table#gvContractors')[0][0][0]]
    headers = [header_conv[h] for h in th]
    for tr in x('table#gvContractors')[0][0][1:-1]:
        if len(tr.getchildren()) != len(th):
            sys.stderr.write('Warning len mismatch: %d != %d\n' %
                             (len(tr.getchildren()), len(th)))
        l.append(dict(zip(headers, [e.text_content() for e in tr])))
    return l

# Starting from the main page, we will get a page at a time and try getting the
# one we want by clicking the paging links.

def is_postback_link(link):
    return link.get_attribute('href').startswith(u"javascript:__doPostBack")

def scrape(browser):
    rows = []
    next_page_index = 1
    while True:
        sys.stderr.write('Dumping page %3d\n' % next_page_index)
        rows += ParseOnePage(pyquery.PyQuery(browser.page_source))
        next_page_index += 1
        links = browser.find_elements_by_xpath("//a")

        # Skip first '...' which points back.
        if links[0].text == '...':
            links = links[1:]

        for link in links:
            #print "<%s> :%s:" % (link.get_attribute('href'),link.text)
            if is_postback_link(link):
                last_postback_link = link
                # We blindly assume that the last '...' link is ours if we did
                # not find our target in the previous ones.
                # nxt = link.get_attribute('href').split("'")[3].split('$')[1]
                # print nxt
                if (match_int(link.text, next_page_index) or
                    link.text == "..."):
                    link.click()
                    time.sleep(3)
                    break
        else:
            # We did not find the link we looked for. Either this is the last
            # page, or something went wrong.  We recognize the last page as the
            # last postback one with no "..." as last link, preferrably with
            # last link pointing to previous page, i.e. next_page_index-2.
            if match_int(last_postback_link.text, next_page_index - 2):
                return True, rows
            browser.save_screenshot('screen.png')
            return False, rows

def add_zeros(x):
    return "0"*(max(0,9-len(x))) + x

def main(output):
    dcap = dict(webdriver.DesiredCapabilities.PHANTOMJS)
    dcap["phantomjs.page.settings.userAgent"] = (
         "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
         "(KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36")
    browser = webdriver.PhantomJS(desired_capabilities = dcap)
    browser.set_window_size(1200, 800)
    browser.get(moital_contractors_url)

    success, rows = scrape(browser)

    print success
    if success:
        out = file(output,'w')
        for row in rows:
            row = { 'id': add_zeros(row['company_id']), 'name': row['company_name'], 'moital_contractor':row }
            out.write(json.dumps(row,sort_keys=True)+'\n')
        return
    raise RuntimeError("Something went wrong!")

class scrape_moital_contractors(object):

    def process(self,input,output):
        main(output)

if __name__=="__main__":
    main('moital.jsons')
