#!/usr/bin/python
#encoding: utf8
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

class extended_data_web_page_base:
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


        #print 'loaded extended data %s in %f secs' % (url, time.time() - start_time)


class search_web_page_base:
    @classmethod
    def get_publishers( cls ):
        i = 0
        while True:
            try:
                return cls().get_options('publisher')
            except expected_exceptions, e:
                i += 1
                print "get_publishers: Got %s, retrying (%d)" % (e,i)
                time.sleep( min( [5*i, 60] ) )


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
        d.setdefault( 'url', self.search_page_url )


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
            return [int(e.xpath('@value')[0].extract()) for e in self.must_exist_xpath( self.publisher_option_xpath ) if int(e.xpath('@value')[0].extract()) != 0]
        else:
            raise NotImplementedError()

    def option_value( self, option_name, option_index ):
        if option_name == 'publisher':
            ret = self.must_exist_xpath( self.publisher_option_xpath + '[@value="%d"]/@title' % option_index  )
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

    def is_single_page( self ):
        r = self.result_indexes()
        return r['total'] <= 10



    def curr_page_num( self ):
        if self.is_single_page():
            return 1

        return int( self.must_exist_xpath( self.results_table_base_xpath + '/tr[%d]/td/div/div/div[3]/span/text()' % (self.num_of_rows() + 2) )[0].extract() )

    def num_of_rows( self ):

        if self.is_single_page():
            d = 1
        else:
            d = 2

        # one row for the heading, one for the page nums
        return len(self.sel.xpath( self.results_table_base_xpath + '/tr' )) - d

    def go_to_page_num( self, page_num ):

        try:
            self.curr_page_num()
            page_valid = True
        except expected_exceptions, e:
            page_valid = False
        
        if not page_valid:
            print "go_to_page_num: need to reconnect..."
            self.initialize_web_page()

        while self.curr_page_num() != page_num:

            next_pages = self.get_next_pages()

            distances = [abs(page_num - page['page_num']) for page in next_pages]

            closest = distances.index( min(distances) )
            expected_page = next_pages[closest]['page_num']

            if page_num != expected_page:
                print 'on the way to page %d going to page %d' % ( page_num, expected_page )

            if next_pages[closest]['page_num'] < self.curr_page_num():
                raise AssertionError()

            self.fill_form( {'__EVENTTARGET':next_pages[closest]['target']} )
            if self.curr_page_num() != expected_page:

                # sometimes this happens...
                print "expected to reach page %d but reached page %d. restarting search." % (expected_page, self.curr_page_num())
                self.initialize_web_page()

    def extract_page_urls( self ):

        start_time = time.time()

        ret = []

        for row_i in xrange(self.num_of_rows()):
            data_elems = self.must_exist_xpath( self.results_table_base_xpath + '/tr[%d]/td' % (row_i+2) )
            if len(data_elems) != self.expected_table_columns:
                raise NoSuchElementException( 'wrong number of elems in row %d' % len(data_elems) )

            url = self.must_exist_xpath( self.url_xpath % (row_i+2) )[0].extract()
            if url.startswith( '/' ):
                url = 'http://www.mr.gov.il' + url

            ret.append( url )

        print 'parsed table page in %f secs' % (time.time() - start_time)

        return ret


    @classmethod
    def iter_publisher_urls( cls, publisher ):
        records_per_page = 10
        
        i = 0
        while True:
            try:
                web_page = cls( publisher_index=publisher )
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

                    import traceback
                    traceback.print_exc()

                    i += 1
                    print "iter_publisher_urls(%d, %d): Got %s, retrying (%d)" % (publisher, page_num, repr(e),i)
                    time.sleep( min( [5*i, 60] ) )

                    #if i >= 20:
                    #    import pdb; pdb.set_trace()


            for url in urls:
                yield page_num, total_pages, url


    @classmethod
    def empty_str_is_none( cls, record, field_name ):
        if field_name in record:
            if type(record[field_name]) in [str,unicode]:
                if len(record[field_name].strip()) == 0:
                    record[field_name] = None

    @classmethod
    def field_to_int( cls, record, field_name ):
        if type(record[field_name]) in [int, long, float]:
            return

        if record[field_name] is None:
            return None

        record[field_name] = record[field_name].replace(',','')
        if '.' in record[field_name]:
            record[field_name] = float(record[field_name])
        else:
            record[field_name] = long(record[field_name])
    @classmethod
    def zero_is_none( cls, record, field_name ):
        if field_name in record:
            if record[field_name] == 0:
                record[field_name] = None
    @classmethod
    def format_documents_time( cls, record ):
        for d in record['documents']:
            if isinstance(d['update_time'], str) or isinstance(d['update_time'], unicode):
                
                # "taarich idkoon mismach:   11:11 05/11/2014"
                
                time, date = d['update_time'].split(' ')[-2:]
                d['update_time'] = {'time':time, 'date':date}


    @classmethod
    def scrape( cls, output_filename, since=None ):

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

        publishers = cls.get_publishers()

        for publisher_index, publisher in enumerate(publishers):
            for page_num, total_pages, url in cls.iter_publisher_urls( publisher ):

                start_time = time.time()

                i = 0
                while True:
                    try:
                        web_page = cls.extended_data_web_page_cls()
                        web_page.go_to_url( url )
                        record = web_page.extract_page_data()
                        break
                    except expected_exceptions, e:
                        i += 1
                        print "scrape: Got %s, retrying (%d)" % (e,i)
                        time.sleep( min( [5*i, 60] ) )
                    
                record = cls.process_record(record)

                if since is not None:
                    if numerate_date(record['last_update_date']) < since:
                        break

                f.write( json.dumps(record) + '\n' )

                print "loaded %s publisher %d %d/%d page %d/%d took %.2f secs" % (url, publisher, publisher_index + 1, len(publishers), page_num, total_pages, time.time() - start_time)

        f.close()


    @classmethod
    def rescrape( cls, input_filename, output_filename ):

        in_f = open( input_filename, 'r' )
        out_f = open( output_filename, 'w' )

        for l in in_f.xreadlines():

            start_time = time.time()

            rec = json.loads(l)
            url = rec['url']
            
            i = 0
            while True:
                try:
                    web_page = cls.extended_data_web_page_cls()
                    web_page.go_to_url( url )
                    record = web_page.extract_page_data()
                    break
                except expected_exceptions, e:
                    i += 1
                    print "rescrape: Got %s, retrying (%d)" % (e,i)
                    time.sleep( min( [5*i, 60] ) )
        
            record = cls.process_record(record)

            print "loaded %s took %.2f secs" % (url, time.time() - start_time)

            out_f.write( json.dumps( record ) + '\n' )

        in_f.close()
        out_f.close()








def test1( search_web_page_cls ):
    publishers = search_web_page_cls.get_publishers()
    web_page = search_web_page_cls( publisher_index=publishers[0] )
    result_indexes = web_page.result_indexes()
    total_pages = (result_indexes['total'] + (10-1)) / 10
    total_records = result_indexes['total']

    print 'total_pages', total_pages
    print 'total_records', total_records

def test2():
    for url in iter_urls():
        print url
