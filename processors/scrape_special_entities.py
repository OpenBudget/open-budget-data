import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv

def prepare(driver):
    driver.get("http://www.misim.gov.il/mm_lelorasham/firstPage.aspx")
    element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "RadioBakasha1"))
                )
    element.click()

slugs = {u"  \u05ea\u05d0\u05d2\u05d9\u05d3\u05d9 \u05d4\u05d0\u05d6\u05d5\u05e8  (\u05d9\u05d5''\u05e9 )": 'west_bank_corporation',
 u'\u05d0\u05d9\u05d2\u05d5\u05d3\u05d9 \u05e2\u05e8\u05d9\u05dd': 'conurbation',
 u'\u05d0\u05d9\u05d2\u05d5\u05d3\u05d9\u05dd \u05de\u05e7\u05e6\u05d5\u05e2\u05d9\u05d9\u05dd': 'professional_association',
 u'\u05d2\u05d5\u05e4\u05d9\u05dd \u05e2"\u05e4 \u05d3\u05d9\u05df': 'law_mandated_organization',
 u'\u05d4\u05e7\u05d3\u05e9 \u05d1\u05d9\u05ea \u05d3\u05d9\u05df \u05d3\u05ea\u05d9': 'religious_court_sacred_property',
 u'\u05d5\u05d5\u05e2\u05d3\u05d9\u05dd \u05de\u05e7\u05d5\u05de\u05d9\u05d9\u05dd \u05d1\u05d9\u05e9\u05d5\u05d1\u05d9\u05dd': 'local_community_committee',
 u'\u05d5\u05e2\u05d3\u05d5\u05ea \u05de\u05e7\u05d5\u05de\u05d9\u05d5\u05ea \u05dc\u05ea\u05db\u05e0\u05d5\u05df': 'local_planning_committee',
 u'\u05d5\u05e2\u05d3\u05d9 \u05d1\u05ea\u05d9\u05dd': 'house_committee',
 u'\u05d7\u05d1\u05e8\u05d5\u05ea \u05d7\u05d5\u05e5 \u05dc\u05d0 \u05e8\u05e9\u05d5\u05de\u05d5\u05ea': 'foreign_company',
 u'\u05de\u05e9\u05e8\u05d3\u05d9 \u05de\u05de\u05e9\u05dc\u05d4': 'government_office',
 u'\u05e0\u05e6\u05d9\u05d2\u05d5\u05d9\u05d5\u05ea \u05d6\u05e8\u05d5\u05ea': 'foreign_representative',
 u'\u05e7\u05d5\u05e4\u05d5\u05ea \u05d2\u05de\u05dc': 'provident_fund',
 u'\u05e8\u05d5\u05d1\u05e2\u05d9\u05dd \u05e2\u05d9\u05e8\u05d5\u05e0\u05d9\u05d9\u05dd': 'municipal_precinct',
 u'\u05e8\u05e9\u05d5\u05d9\u05d5\u05ea \u05de\u05e7\u05d5\u05de\u05d9\u05d5\u05ea': 'municipality',
 u'\u05e8\u05e9\u05d5\u05d9\u05d5\u05ea \u05e0\u05d9\u05e7\u05d5\u05d6': 'drainage_authority',
 u'\u05e8\u05e9\u05d9\u05de\u05d5\u05ea \u05dc\u05e8\u05e9\u05d5\u05d9\u05d5\u05ea \u05d4\u05de\u05e7\u05d5\u05de\u05d9\u05d5\u05ea': 'municipal_parties',
 u'\u05e9\u05d9\u05e8\u05d5\u05ea\u05d9 \u05d1\u05e8\u05d9\u05d0\u05d5\u05ea': 'health_service',
 u'\u05e9\u05d9\u05e8\u05d5\u05ea\u05d9 \u05d3\u05ea': 'religion_service'}

if __name__=="__main__":
    driver = webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true'])
    driver.set_window_size(1200, 800)
    prepare(driver)
    select = driver.find_element_by_id("DropdownlistSugYeshut")
    options = {}
    for option in select.find_elements_by_tag_name('option')[1:]:
        options[option.get_attribute('value')] = option.text

    out = csv.writer(file('out.csv','w'))

    for selection in options.keys():
        prepare(driver)
        driver.find_element_by_css_selector('option[value="%s"]' % selection).click()
        driver.find_element_by_id('btnHipus').click()
        data = []
        while True:
            print slugs[options[selection]]
            element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "#dgReshima tr.row1 "))
                        )
            rows = driver.find_elements_by_css_selector('#dgReshima tr.row1, #dgReshima tr.row2')
            for row in rows:
                if row.get_attribute('class') in ('row1','row2'):
                    datum = [slugs[options[selection]]]
                    datum.extend([x.text.encode('utf8') for x in row.find_elements_by_tag_name('td')])
                    data.append(datum)

            try:
                nextButton = driver.find_element_by_id('btnHaba')
                nextButton.click()
                time.sleep(1)
            except:
                out.writerows(data)
                break
