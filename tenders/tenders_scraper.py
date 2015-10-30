#!/usr/bin/python
#encoding: utf8
import mr_gov_il
import time
import pprint
import json
import os
import copy
import shutil
import requesocks as requests
#import requests
from scrapy.selector import Selector
import urllib3
import sys
from datetime import datetime, timedelta

class tender_extended_data_web_page(mr_gov_il.extended_data_web_page_base):
    def extract_page_data( self ):
        #start_time = time.time()

        sel = Selector(text=self.response.text)

        ret = {}

        if self.publication_id is not None:
            ret['publication_id'] = self.publication_id

        found_fields = 0

        for field_name, xpath in [('description', '//*[@id="ctl00_PlaceHolderMain_lbl_PublicationName"]'),
                                  ('publisher', '//*[@id="ctl00_PlaceHolderMain_lbl_Publisher"]'),
                                  ('publish_date', '//*[@id="ctl00_PlaceHolderMain_lbl_PublishDate"]'),
                                  ('publication_id', '//*[@id="ctl00_PlaceHolderMain_lbl_SERIAL_NUMBER"]'),
                                  ('status', '//*[@id="ctl00_PlaceHolderMain_lbl_PublicationSTATUS"]'),
                                  ('last_update_date', '//*[@id="ctl00_PlaceHolderMain_lbl_UpdateDate"]'),
                                  ('subjects', '//*[@id="ctl00_PlaceHolderMain_lbl_PublicationSUBJECT"]'),
                                  ('claim_date', '//*[@id="ctl00_PlaceHolderMain_lbl_ClaimDate"]') ]:

            if len(sel.xpath(xpath+'/text()')) == 0:
                ret[field_name] = None
            else:
                found_fields += 1
                try:
                    ret[field_name] = sel.xpath(xpath+'/text()')[0].extract()
                except:
                    print "failed %s %s" % (field_name, url)
                    raise


        if found_fields == 0:
            raise NoSuchElementException()

        if None in [ret["last_update_date"]]:
            raise NoSuchElementException()

        ret['url'] = self.url
        ret['documents'] = []
        links = sel.xpath('//*[@id="ctl00_PlaceHolderMain_pnl_Files"]/div/div/div[2]/a')
        update_times = sel.xpath('//*[@id="ctl00_PlaceHolderMain_pnl_Files"]/div/div/div[1]')

        if len(links) != len(update_times):
            raise NoSuchElementException()

        for i in xrange( len(links) ):
            ret['documents'].append( {'description':links[i].xpath('text()')[0].extract(),
                                      'link':'http://www.mr.gov.il' + links[i].xpath('@href')[0].extract(),
                                      'update_time':update_times.xpath('text()')[0].extract()
                                      } )

        #print 'parsed exended data in %f secs' % (time.time() - start_time)

        return ret

class tender_search_web_page(mr_gov_il.search_web_page_base):
    extended_data_web_page_cls = tender_extended_data_web_page
    search_page_url = 'http://www.mr.gov.il/OfficesTenders/Pages/SearchOfficeTenders.aspx'
    publisher_option_xpath = '//*[@id="ctl00_m_g_7b9ec4d5_a2ee_4fc4_8523_cd0a65f2d290_ctl00_ddlPublisher"]/option'
    results_table_base_xpath = '//*[@id="ctl00_m_g_7b9ec4d5_a2ee_4fc4_8523_cd0a65f2d290_ctl00_grvMichrazim"]'
    url_xpath = results_table_base_xpath + '/tr[%d]/td[2]/a/@href'
    expected_table_columns = 7

    def fill_form( self, d={} ):
        form_data = {
            '__EVENTTARGET':'',
            '__EVENTARGUMENT':'',
        }

        for form_data_elem in self.must_exist_xpath('//*[@id="aspnetForm"]/input'):
            form_data[form_data_elem.xpath('@name')[0].extract()] = form_data_elem.xpath('@value')[0].extract()

        for form_data_elem in self.must_exist_xpath('//*[@id="WebPartWPQ3"]//select'):
            form_data[form_data_elem.xpath('@name')[0].extract()] = 0

        for form_data_elem in self.must_exist_xpath('//*[@id="WebPartWPQ3"]//input'):
            form_data[form_data_elem.xpath('@name')[0].extract()] = ''

        if 'publisher_index' in self.search_params:
            form_data['ctl00$m$g_7b9ec4d5_a2ee_4fc4_8523_cd0a65f2d290$ctl00$ddlPublisher'] = self.search_params['publisher_index']

        form_data.update( d )

        # the clear button was not clicked
        form_data.pop( 'ctl00$m$g_7b9ec4d5_a2ee_4fc4_8523_cd0a65f2d290$ctl00$btnClear' )

        # select all kinds of tenders
        form_data['ctl00$m$g_7b9ec4d5_a2ee_4fc4_8523_cd0a65f2d290$ctl00$chkCanceled'] = 'on'
        form_data['ctl00$m$g_7b9ec4d5_a2ee_4fc4_8523_cd0a65f2d290$ctl00$chkUpdate'] = 'on'
        form_data['ctl00$m$g_7b9ec4d5_a2ee_4fc4_8523_cd0a65f2d290$ctl00$chkNew'] = 'on'
        form_data['ctl00$m$g_7b9ec4d5_a2ee_4fc4_8523_cd0a65f2d290$ctl00$chkEnded'] = 'on'

        form_data['SearchFreeText'] = u'חפש'
        form_data['ctl00_PlaceHolderHorizontalNav_RadMenu1_ClientState'] = ''

        if form_data['__EVENTTARGET']:

            # if a page number was presses, the search button was not clicked
            form_data.pop( 'ctl00$m$g_7b9ec4d5_a2ee_4fc4_8523_cd0a65f2d290$ctl00$btnSearch' )

        # for k in sorted(form_data.keys()):
        #     v = form_data[k]
        #     if len(str(v)) < 20:
        #         print k, '=', repr(v)
        #     else:
        #         print k, '=', repr(v)[:20] + '...'

        self.request( 'post', data=form_data )

    @classmethod
    def process_record( cls, record ):
        # empty_str_is_none( record, 'supplier_id' )
        # field_to_int( record, 'supplier_id' )
        # zero_is_none( record, 'supplier_id' )
        cls.format_documents_time( record )
        
        record['claim_time'], record['claim_date'] = record['claim_date'].split(' ')
        
        return record


if __name__ == "__main__":

    from optparse import OptionParser

    parser = OptionParser( usage='usage: %prog [options] <output filename>' )
    parser.add_option("--rescrape", dest="rescrape", action='store', help='rescrape the urls of a previous scrape', metavar='old_json', default=None)
    parser.add_option("--since", dest="since", action='store', help='since a date or one of: yesterday, last_week, last_year, all_time', default=None)

    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.error( 'must provide an output filename' )

    if options.rescrape:
        tender_search_web_page.rescrape( input_filename=options.rescrape, output_filename=args[0] )
    else:
        tender_search_web_page.scrape( output_filename=args[0], since=options.since )
