#encoding: utf8

import urllib2
import csv
import urllib
import os
import requests
import logging
import time
import hashlib
import hmac

from  BeautifulSoup import BeautifulSoup
import StringIO
import json
import datetime

def decodeAddressToCoordinates(address):
	urlParams = {
			'address': address,
			'sensor': 'false',
	}
	url = 'http://maps.google.com/maps/api/geocode/json?' + urllib.urlencode( urlParams )
	result = requests.get(url).json()
	if 'status' not in result or result['status'] != 'OK':
			return None
	else:
			return {
					'lat': result['results'][0]['geometry']['location']['lat'],
					'lng': result['results'][0]['geometry']['location']['lng']
			}

def get_company_details( company_id ):
	session = requests.Session()
	response = session.request( 'get', url='http://havarot.justice.gov.il/CompaniesList.aspx', timeout=10 )
	soup = BeautifulSoup(response.text)

	form_data = {
	'__EVENTTARGET':'',
	'__EVENTARGUMENT':'',
	}

	for form_data_elem in soup.find( id='aspnetForm' ).findAll( 'input' ):
		attrs = dict( form_data_elem.attrs )
		form_data[attrs['name']] = attrs.get( 'value', '' )

	form_data['ctl00$CPHCenter$txtCompanyNumber'] = str(company_id)

	response = session.request( 'post', url='http://havarot.justice.gov.il/CompaniesList.aspx', data=form_data, timeout=10 )
	soup = BeautifulSoup(response.text)
	if soup.find(id='CPHCenter_GridBlock').find('a') is None:
		return None
	response = session.request( 'get', url='http://havarot.justice.gov.il/CompaniesDetails.aspx?id=%s' % company_id, timeout=10 )
	soup = BeautifulSoup(response.text)

	company_name = soup.find(id="CPHCenter_lblCompanyNameHeb").getText()
	company_status = soup.find(id="CPHCenter_lblStatus").getText()
	company_type = soup.find(id="CPHCenter_lblCorporationType").getText()
	company_government = soup.find(id="CPHCenter_lblGovCompanyType").getText()
	# if company_government == u'חברה לא ממשלתית':
	# 	company_government = False
	# elif company_government == u'חברה ממשלתית':
	# 	company_government = True
	# else:
	# 	print "Unknown company type ",company_government
	# 	company_government = None
	company_limit = soup.find(id="CPHCenter_lblLimitType").getText()
	company_postal_code = soup.find(id="CPHCenter_lblZipCode").getText()

	try:
		company_mafera = soup.find(id="CPHCenter_lblStatusMafera1").getText()
	except IndexError:
		company_mafera = ''


	company_address = ''
	try:
		soup.find(id="CPHCenter_lblStreet").getText()
		company_address = company_address + soup.find(id="CPHCenter_lblStreet").getText() + ' '
	except IndexError:
		company_address = company_address
	try:
		soup.find(id="CPHCenter_lblStreetNumber").getText()
		company_address = company_address + soup.find(id="CPHCenter_lblStreetNumber").getText() + ' '
	except IndexError:
		company_address = company_address
	company_city = ''
	try:
		soup.find(id="CPHCenter_lblCity").getText()
		company_city = soup.find(id="CPHCenter_lblCity").getText()
		company_address = company_address + soup.find(id="CPHCenter_lblCity").getText() + ' '
	except IndexError:
		company_address = company_address
		company_city = ''

	try:
		place = decodeAddressToCoordinates(company_address.encode('utf-8'))
		lat, lng = place.get('lat'), place.get('lng')
	except AttributeError:
		lat, lng = '1','1'

	return {'id':company_id,
			'company_name':company_name,
			'company_status':company_status,
			'company_type':company_type,
			'company_government':company_government,
			'company_limit':company_limit,
			'company_postal_code':company_postal_code,
			'company_mafera':company_mafera,
			'company_address':company_address,
			'company_city':company_city,
			'lat':lat,
			'lng':lng}

class company_scraper(object):
    def process(self,input,output,input_gzipped=False):
		out = None
		for line in open(input):
			line = json.loads(line)
			if line['kind'] == 'company':
				outline = get_company_details(line['id'])
				if out is None:
					out = open(output,'w')
				out.write(json.dumps(outline,sort_keys=True)+'\n')
# ids = get_query_results(392, '8b5a8adca7a83c7578d87e77299a19ad616a4378')
#
# ids_list = []
# for id in ids:
# 	ids_list.append(id.get('entity_id'))
# print len(ids_list)
#
# results = []
#
# i=0
# for id in ids_list:
# 	line = get_company_details(int(id))
# 	if line is not None:
# 		results.append(line)
# 	#print results
# 	#print id
# 	i +=1
# 	if i%100==0:
# 		print i
#
#
# resultFile = open("C:\\Users\\DELL\\Desktop\\company_output.csv",'wb')
# wr = csv.writer(resultFile, dialect='excel')
# wr.writerows(results)
# resultFile.close()
#
# b = datetime.datetime.now()
# c = b - a
# print divmod(c.total_seconds(), 60)
