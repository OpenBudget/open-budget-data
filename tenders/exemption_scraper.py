#!/usr/bin/python
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

def numerate_date( d ):
    if d is None:
        return None
    if d == '-':
        return None
    if type(d) in [int, long, float]:
        return d
    if len(d.strip()) == 0:
        return None

    try:
        day, month, year = [int(x) for x in d.split('/')]
    except:
        print repr(d)
        raise
    return time.mktime( time.struct_time([year, month, day, 0, 0, 0, 0, 0, 0]) )

class NoSuchElementException(Exception):
    pass

expected_exceptions = (urllib3.exceptions.ReadTimeoutError, requests.exceptions.ConnectionError, requests.exceptions.HTTPError, requests.exceptions.SSLError, requests.exceptions.Timeout, NoSuchElementException)

def get_publishers():
    i = 0
    while True:
        try:
            return search_web_page().get_options('publisher')
        except expected_exceptions, e:
            i += 1
            print "get_publishers: Got %s, retrying (%d)" % (e,i)
            time.sleep( min( [5*i, 60] ) )


class search_web_page:
    def __init__( self, **search_params ):
        self.search_params = search_params
        self.session = None

        self.initialize_web_page()

    def request( self, *p, **d ):
        if self.session is None:
            self.session = requests.Session()

            proxy = os.environ.get('PROXY')
            if proxy is not None:
                self.session.proxies = {'http': 'socks5://'+proxy}

        d.setdefault( 'timeout', 180 )
        d.setdefault( 'url', 'http://www.mr.gov.il/ExemptionMessage/Pages/SearchExemptionMessages.aspx' )


        i = 0
        while True:
            try:
                self.response = self.session.request( *p, **d )
                break
            except Exception,e:
                i += 1
                print "search_web_page.request: Got %s, retrying (%d)" % (e,i)
                time.sleep( min( [5*i, 60] ) )


        self.sel = Selector(text=self.response.text)


    def initialize_web_page( self ):

        start_time = time.time()
        sys.stdout.write( 'connecting to search page (%s)... ' % (str(self.search_params)) )
        sys.stdout.flush()

        self.request( 'get' )

        if self.search_params:
            self.search( **self.search_params )

        print "done %.2f sec" % (time.time() - start_time)

    def is_first_response( self ):
        return self.result_indexes() == {'range':[1,10], 'total':100}

    def result_indexes( self ):
        records_range_str = self.must_exist_xpath( '//*[@class="resultsSummaryDiv"]/text()' )[0].extract()
        # "tozaot 1-10 mitoch 100 reshumot

        if len(records_range_str.split(' ')) == 3: # lo nimtzeu reshoomot
            return {'range':[0,0], 'total':0}

        return {'range':[int(x) for x in records_range_str.split(' ')[1].split('-')], 'total':int((records_range_str.split(' ')[3]))}

    def must_exist_xpath( self, *p, **d ):
        ret = self.sel.xpath( *p, **d )
        if len(ret) == 0:
            raise NoSuchElementException()
        return ret

    def get_next_pages( self ):

        ret = []
        for elem in self.must_exist_xpath( '//*[@class="resultsPagingNumber"]' ):

            # href = javascript:WebForm_DoPostBackWithOptions(new WebForm_PostBackOptions("ctl00$m$g_cf609c81_a070_46f2_9543_e90c7ce5195b$ctl00$grvMichrazim$ctl13$ctl01", "", true, "", "", false, true))
            # extracting the ctl00$m$g_...ctl13$ctl01
            target = elem.xpath('@href')[0].extract()
            target = target.split( '(' )[2].split('"')[1]


            ret.append( {'page_num':int(elem.xpath('@title')[0].extract()),
                         'target':target} )

        return ret

    def get_options( self, option_name ):
        if option_name == 'publisher':
            return [int(e.xpath('@value')[0].extract()) for e in self.must_exist_xpath( '//*[@id="ctl00_m_g_cf609c81_a070_46f2_9543_e90c7ce5195b_ctl00_ddlPublisher"]/option' ) if int(e.xpath('@value')[0].extract()) != 0]
        else:
            raise NotImplementedError()

    def option_value( self, option_name, option_index ):
        if option_name == 'publisher':
            ret = self.must_exist_xpath( '//*[@id="ctl00_m_g_cf609c81_a070_46f2_9543_e90c7ce5195b_ctl00_ddlPublisher"]/option[@value="%d"]/@title' % option_index  )
            if len(ret) != 1:
                raise AssertionError( 'no publisher number %d' % option_index )
            return ret[0].extract()
        else:
            raise NotImplementedError()

    def search( self, **search_params ):

        search_params.setdefault( 'publisher_index', '' )
        self.search_params = search_params

        ret = {'publisher':
               self.option_value('publisher', self.search_params['publisher_index'])}

        self.fill_form()

        return ret

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
            form_data['ctl00$m$g_cf609c81_a070_46f2_9543_e90c7ce5195b$ctl00$ddlPublisher'] = self.search_params['publisher_index']

        form_data.update( d )

        # the clear button was not clicked
        form_data.pop( 'ctl00$m$g_cf609c81_a070_46f2_9543_e90c7ce5195b$ctl00$btnClear' )

        if form_data['__EVENTTARGET']:

            # if a page number was presses, the search button was not clicked
            form_data.pop( 'ctl00$m$g_cf609c81_a070_46f2_9543_e90c7ce5195b$ctl00$btnSearch' )

        # for k in sorted(form_data.keys()):
        #     v = form_data[k]
        #     if len(str(v)) < 20:
        #         print k, '=', repr(v)
        #     else:
        #         print k, '=', repr(v)[:20] + '...'


        self.request( 'post', data=form_data )


    def is_single_page( self ):
        r = self.result_indexes()
        return r['total'] <= 10


    def curr_page_num( self ):
        if self.is_single_page():
            return 1

        return int( self.must_exist_xpath( '//*[@id="ctl00_m_g_cf609c81_a070_46f2_9543_e90c7ce5195b_ctl00_grvMichrazim"]/tr[%d]/td/div/div/div[3]/span/text()' % (self.num_of_rows() + 2) )[0].extract() )

    def num_of_rows( self ):

        if self.is_single_page():
            d = 1
        else:
            d = 2

        # one row for the heading, one for the page nums
        return len(self.sel.xpath( '//*[@id="ctl00_m_g_cf609c81_a070_46f2_9543_e90c7ce5195b_ctl00_grvMichrazim"]/tr' )) - d

    def go_to_page_num( self, page_num ):

        while self.curr_page_num() != page_num:

            next_pages = self.get_next_pages()

            distances = [abs(page_num - page['page_num']) for page in next_pages]

            closest = distances.index( min(distances) )
            expected_page = next_pages[closest]['page_num']

            print 'on the way to page %d going to page %d' % ( page_num, expected_page )

            if next_pages[closest]['page_num'] < self.curr_page_num():
                raise AssertionError()

            self.fill_form( {'__EVENTTARGET':next_pages[closest]['target']} )
            if self.curr_page_num() != expected_page:

                # sometimes this happens...
                print "expected to reach page %d but reached page %d. restarting search." % (expected_page, self.curr_page_num())
                self.initialize_web_page()

    heading_name_map = {
        u'\u05de\u05e4\u05e8\u05e1\u05dd':'publisher',
        u'\u05ea\u05e7\u05e0\u05d4':'regulation',
        u'\u05d4\u05d9\u05e7\u05e3 \u05db\u05e1\u05e4\u05d9 \u05d1\u05e9"\u05d7':'volume',
        u'\u05e9\u05dd \u05e1\u05e4\u05e7':'supplier',
        u'\u05e0\u05d5\u05e9\u05d0/\u05d9\u05dd':'subjects',
        u'\u05ea\u05d7\u05d9\u05dc\u05ea \u05d4\u05ea\u05e7\u05e9\u05e8\u05d5\u05ea':'start_date',
        u'\u05e1\u05d9\u05d5\u05dd \u05d4\u05ea\u05e7\u05e9\u05e8\u05d5\u05ea':'end_date',
        u'\u05d4\u05d7\u05dc\u05d8\u05d4':'decision'
    }

    heading_order = ['publisher', 'regulation', 'volume', 'supplier', 'subjects', 'start_date', 'end_date', 'decision']

    def validate_headings( self ):
        # titles
        # //*[@id="ctl00_m_g_cf609c81_a070_46f2_9543_e90c7ce5195b_ctl00_grvMichrazim"]/tbody/tr[1]/th

        start_time = time.time()

        for i, e in enumerate( self.must_exist_xpath( '//*[@id="ctl00_m_g_cf609c81_a070_46f2_9543_e90c7ce5195b_ctl00_grvMichrazim"]/tr[1]/th' ) ):
            hebrew_title = e.xpath('text()')[0].extract()
            if hebrew_title not in self.heading_name_map:
                raise NoSuchElementException( 'unknown heading %s' % repr(hebrew_title) )
            title = self.heading_name_map[hebrew_title]
            if self.heading_order.index( title ) != i:
                raise NoSuchElementException( 'heading %s expected at index %d but is at index %d' % (title, self.heading_order.index( title ), i) )

        print 'wasted %f secs on heading validation' % (time.time() - start_time )

    def extract_page_urls( self ):

        start_time = time.time()

        #self.validate_headings()

        ret = []

        for row_i in xrange(self.num_of_rows()):
            data_elems = self.must_exist_xpath( '//*[@id="ctl00_m_g_cf609c81_a070_46f2_9543_e90c7ce5195b_ctl00_grvMichrazim"]/tr[%d]/td' % (row_i+2) )
            if len(data_elems) != 8:
                raise NoSuchElementException( 'wrong number of elems in row' )

            if len(data_elems) != len(self.heading_order):
                raise NoSuchElementException( 'wrong number of elems in row' )

            url = self.must_exist_xpath( '//*[@id="ctl00_m_g_cf609c81_a070_46f2_9543_e90c7ce5195b_ctl00_grvMichrazim"]/tr[%d]/td[1]/a/@href' % (row_i+2) )[0].extract()
            if url.startswith( '/' ):
                url = 'http://www.mr.gov.il' + url

            ret.append( url )

        print 'parsed table page in %f secs' % (time.time() - start_time)

        return ret


class extended_data_web_page:
    def __init__( self, rate_limit=None ):
        self.session = requests.Session()
        proxy = os.environ.get('PROXY')
        if proxy is not None:
            self.session.proxies = {'http': 'socks5://'+proxy}
        self.rate_limit = rate_limit
        self.publication_id = None

    def go_to_publication_id( self, publication_id ):
        self.publication_id = publication_id

        url = exemption_record.get_record( publication_id=publication_id )['url']

        self.go_to_url( url )

    def go_to_url( self, url ):

        self.url = url
        if self.rate_limit is not None:
            self.rate_limit.rate_limit()
        start_time = time.time()


        i = 0
        while True:
            try:
                self.response = self.session.request( 'get', url=url, timeout=10 )
                break
            except Exception,e:
                i += 1
                print "extended_data_web_page.go_to_url: Got %s, retrying (%d)" % (e,i)
                time.sleep( min( [5*i, 60] ) )


        print 'loaded extended data %s in %f secs' % (url, time.time() - start_time)


    def extract_page_data( self ):
        #start_time = time.time()

        sel = Selector(text=self.response.text)

        ret = {}

        if self.publication_id is not None:
            ret['publication_id'] = self.publication_id

        found_fields = 0

        for field_name, xpath in [('description', '//*[@id="ctl00_PlaceHolderMain_lbl_PublicationName"]'),
                                  ('supplier_id', '//*[@id="ctl00_PlaceHolderMain_lbl_SupplierNum"]'),
                                  ('supplier', '//*[@id="ctl00_PlaceHolderMain_lbl_SupplierName"]'),
                                  ('contact', '//*[@id="ctl00_PlaceHolderMain_lbl_ContactPersonName"]'),
                                  ('publisher', '//*[@id="ctl00_PlaceHolderMain_lbl_PUBLISHER"]'),
                                  ('contact_email', '//*[@id="ctl00_PlaceHolderMain_lbl_ContactPersonEmail"]'),
                                  ('claim_date', '//*[@id="ctl00_PlaceHolderMain_lbl_ClaimDate"]'),
                                  ('last_update_date', '//*[@id="ctl00_PlaceHolderMain_lbl_UpdateDate"]'),
                                  ('reason', '//*[@id="ctl00_PlaceHolderMain_lbl_PtorReason"]'), 
                                  ('source_currency', '//*[@id="ctl00_PlaceHolderMain_lbl_Currency"]'),
                                  ('regulation', '//*[@id="ctl00_PlaceHolderMain_lbl_Regulation"]'),
                                  ('volume', '//*[@id="ctl00_PlaceHolderMain_lbl_TotalAmount"]'),
                                  ('subjects', '//*[@id="ctl00_PlaceHolderMain_lbl_PublicationSUBJECT"]'),
                                  ('start_date', '//*[@id="ctl00_PlaceHolderMain_lbl_StartDate"]'),
                                  ('end_date', '//*[@id="ctl00_PlaceHolderMain_lbl_EndDate"]'),
                                  ('decision', '//*[@id="ctl00_PlaceHolderMain_lbl_Decision"]'),
                                  ('page_title', '//*[@id="ctl00_PlaceHolderMain_lbl_PublicationType"]') ]:

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


def test1():
    publishers = get_publishers()
    web_page = search_web_page( publisher_index=publishers[0] )
    result_indexes = web_page.result_indexes()
    total_pages = (result_indexes['total'] + (10-1)) / 10
    total_records = result_indexes['total']

    print 'total_pages', total_pages
    print 'total_records', total_records

def test2():
    for url in iter_urls():
        print url

def iter_publisher_urls( publisher ):
    records_per_page = 10

    i = 0
    while True:
        try:
            web_page = search_web_page( publisher_index=publisher )
            result_indexes = web_page.result_indexes()
            break
        except expected_exceptions, e:
            i += 1
            print "iter_publisher_urls(init): Got %s, retrying (%d)" % (e,i)
            time.sleep( min( [5*i, 60] ) )
            

    total_pages = (result_indexes['total'] + (records_per_page-1)) / records_per_page
    
    for page_num in xrange(1,total_pages + 1):

        i = 0
        while True:
            try:
                web_page.go_to_page_num( page_num )
                urls = web_page.extract_page_urls()
                break
            except expected_exceptions, e:
                i += 1
                print "iter_publisher_urls: Got %s, retrying (%d)" % (e,i)
                time.sleep( min( [5*i, 60] ) )

        for url in urls:
            yield url

def empty_str_is_none( record, field_name ):
    if field_name in record:
        if type(record[field_name]) in [str,unicode]:
            if len(record[field_name].strip()) == 0:
                record[field_name] = None
def field_to_int( record, field_name ):
    if type(record[field_name]) in [int, long, float]:
        return

    if record[field_name] is None:
        return None

    record[field_name] = record[field_name].replace(',','')
    if '.' in record[field_name]:
        record[field_name] = float(record[field_name])
    else:
        record[field_name] = long(record[field_name])
def zero_is_none( record, field_name ):
    if field_name in record:
        if record[field_name] == 0:
            record[field_name] = None
def format_documents_time( record ):
    for d in record['documents']:
        if isinstance(d['update_time'], str) or isinstance(d['update_time'], unicode):

            # "taarich idkoon mismach:   11:11 05/11/2014"

            time, date = d['update_time'].split(' ')[-2:]
            d['update_time'] = {'time':time, 'date':date}


def process_record( record ):
    empty_str_is_none( record, 'supplier_id' )
    field_to_int( record, 'supplier_id' )
    zero_is_none( record, 'supplier_id' )
    format_documents_time( record )
    return record

def scrape( output_filename, since=None ):

    if since is not None:
        if since == 'yesterday':
            yesterday = datetime.now() - timedelta(days=2)
            since = yesterday.strftime('%d/%m/%y')
        
        elif since == 'last_week':
            yesterday = datetime.now() - timedelta(days=8)
            since = yesterday.strftime('%d/%m/%y')
        
        elif since == 'last_year':
            yesterday = datetime.now() - timedelta(days=366)
            since = yesterday.strftime('%d/%m/%y')
        
        elif since == 'all_time':
            since = '1/1/2010'
    
        since = numerate_date( since )

    f = open( output_filename, 'w' )

    publishers = get_publishers()

    for publisher in publishers:
        for url in iter_publisher_urls( publisher ):

            i = 0
            while True:
                try:
                    web_page = extended_data_web_page()
                    web_page.go_to_url( url )
                    record = web_page.extract_page_data()
                    break
                except expected_exceptions, e:
                    i += 1
                    print "scrape: Got %s, retrying (%d)" % (e,i)
                    time.sleep( min( [5*i, 60] ) )
                    
            record = process_record(record)

            if since is not None:
                if numerate_date(record['last_update_date']) < since:
                    break

            f.write( json.dumps(record) + '\n' )

    f.close()

def rescrape( input_filename, output_filename ):

    in_f = open( input_filename, 'r' )
    out_f = open( output_filename, 'w' )

    for l in in_f.xreadlines():
        rec = json.loads(l)
        url = rec['url']

        i = 0
        while True:
            try:
                web_page = extended_data_web_page()
                web_page.go_to_url( url )
                record = web_page.extract_page_data()
                break
            except expected_exceptions, e:
                i += 1
                print "rescrape: Got %s, retrying (%d)" % (e,i)
                time.sleep( min( [5*i, 60] ) )
        
        record = process_record(record)
        out_f.write( json.dumps( record ) + '\n' )

    in_f.close()
    out_f.close()


if __name__ == "__main__":

    from optparse import OptionParser

    parser = OptionParser( usage='usage: %prog [options] <output filename>' )
    parser.add_option("--rescrape", dest="rescrape", action='store', help='rescrape the urls of a previous scrape', metavar='old_json', default=None)
    parser.add_option("--since", dest="since", action='store', help='since a date or one of: yesterday, last_week, last_year, all_time', default=None)

    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.error( 'must provide an output filename' )

    if options.rescrape:
        rescrape( input_filename=options.rescrape, output_filename=args[0] )
    else:
        scrape( output_filename=args[0], since=options.since )
