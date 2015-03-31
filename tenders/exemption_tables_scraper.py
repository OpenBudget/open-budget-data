#!/usr/bin/python
from selenium import webdriver
from selenium.webdriver.support.ui import Select
import selenium.common.exceptions
import base_scraper
import time
import pprint
import json
import os
import copy
import shutil
import requests
from scrapy.selector import Selector
from post_processing import field_to_int, zero_is_none, add_history_field
from exemption_record import update_data, exemption_json_to_csv


# TODO: when there is a mismatch in the publisher scraper params, rm -rf the dir and restart
# TODO: only run between 6pm to 6am? rate limit after 6am?
# TODO: support multi processes? split the publisher scraping with different page steps? scrape publishers in parallel?
# TODO: after completing the scraping, wrap it all into a json file with the current date
# TODO: save the scraping meta data? save the start time and end time per publisher?
# TODO: post processing:
#         date parsing
#         volume str to int
#         fill the suppliers name which end in '...'
#         the id of the record can be extracted from the url
#         diff between yesterday and today by the id
#         mark the records with the scraper name, extraction date, scraper version
# TODO: subprocess into the scraper because it sometimes gets into a timeout loop which is only stopped after restarting and stop scraping after a few timeouts
# TODO: run the extended scraper for the new entries right imediately


class counts_scraper(base_scraper.base_scraper):
    def __init__( self, base_path ):
        base_scraper.base_scraper.__init__( self, base_path=os.path.join(base_path, 'publisher_counts') )

    def __repr__( self ):
        return 'counts_scraper()'

    def get_state( self ):
        return {'total_pages':self.web_page.num_of_options('publisher')}

    def go_to_page_num( self, page_num ):
        self.searched = self.web_page.search( publisher_index=(page_num-1) )

    def extract_records( self ):
        return [ {'total':self.web_page.result_indexes()['total'], 'publisher':self.searched['publisher'], 'index':(self.curr_page - 1)} ]


# scraper
class publisher_scraper(base_scraper.base_scraper):
    def __init__( self, base_path, publisher_index ):

        self.publisher_index = publisher_index

        base_scraper.base_scraper.__init__( self, base_path=os.path.join( base_path, '%d' % self.publisher_index ) )

    def __repr__( self ):
        return 'publisher_scraper( %d )' % (self.publisher_index)

    def get_state( self ):
        self.web_page = search_web_page( publisher_index=self.publisher_index )
        result_indexes = self.web_page.result_indexes()

        ret = {}

        ret['publisher_name'] = self.web_page.option_value( 'publisher', self.publisher_index )

        records_per_page = 10

        if result_indexes['range'][1] > records_per_page:
            raise AssertionError( 'more records per page than expected' )

        ret['total_pages'] = (result_indexes['total'] + (records_per_page-1)) / records_per_page
        ret['total_records'] = result_indexes['total']

        return ret

    def reset_scraper( self ):
        print "deleting %s" % self.base_path
        shutil.rmtree( self.base_path )
        base_scraper.rec_mkdir( self.base_path )

    def go_to_page_num( self, page_num ):
        self.web_page.go_to_page_num( page_num )

    def extract_records( self ):
        return self.web_page.extract_page_data()

class search_web_page:
    def __init__( self, rate_limit=None, **search_params ):
        self.rate_limit = rate_limit
        self.search_params = search_params
        self.initialize_web_page()

    def initialize_web_page( self ):
        print "initializing browser..."
        proxy = os.environ.get('PROXY')
        if proxy is not None:
            service_args = [
                '--proxy=%s' % proxy,
                '--proxy-type=socks5',
            ]
            self.driver = webdriver.PhantomJS(service_args=service_args)
        else:
            self.driver = webdriver.PhantomJS()
        self.driver.set_window_size(1024, 768)
        self.driver.set_script_timeout( 30 )
        self.driver.set_page_load_timeout( 30 )
        self.driver.get('http://www.mr.gov.il/ExemptionMessage/Pages/SearchExemptionMessages.aspx')
        if self.search_params:
            self.search( **self.search_params )
        print "done"

    def is_first_response( self ):
        return self.result_indexes() == {'range':[1,10], 'total':100}

    def result_indexes( self ):
        records_range_str = self.driver.find_element_by_xpath( '//*[@class="resultsSummaryDiv"]' ).text
        # "tozaot 1-10 mitoch 100 reshumot

        if len(records_range_str.split(' ')) == 3: # lo nimtzeu reshoomot
            return {'range':[0,0], 'total':0}

        return {'range':[int(x) for x in records_range_str.split(' ')[1].split('-')], 'total':int((records_range_str.split(' ')[3]))}

    def get_next_pages( self ):

        ret = []
        for elem in self.driver.find_elements_by_xpath( '//*[@class="resultsPagingNumber"]' ):
            ret.append( {'page_num':int(elem.text),
                         'elem':elem} )

        return ret

    def num_of_options( self, option_name ):
        if option_name == 'publisher':
            return len(Select(self.driver.find_element_by_xpath( '//*[@id="ctl00_m_g_cf609c81_a070_46f2_9543_e90c7ce5195b_ctl00_ddlPublisher"]' )).options)
        else:
            raise NotImplementedError()

    def option_value( self, option_name, option_index ):
        if option_name == 'publisher':
            return Select(self.driver.find_element_by_xpath( '//*[@id="ctl00_m_g_cf609c81_a070_46f2_9543_e90c7ce5195b_ctl00_ddlPublisher"]' )).options[option_index].text
        else:
            raise NotImplementedError()

    def search( self, **search_params ):

        search_params.setdefault( 'publisher_index', 0 )
        self.search_params = search_params

        if self.rate_limit is not None:
            self.rate_limit.rate_limit()

        selector = Select(self.driver.find_element_by_xpath( '//*[@id="ctl00_m_g_cf609c81_a070_46f2_9543_e90c7ce5195b_ctl00_ddlPublisher"]' ))
        selector.select_by_index( self.search_params['publisher_index'] )

        ret = {'publisher':selector.all_selected_options[0].text}

        self.driver.find_element_by_xpath( '//*[@id="ctl00_m_g_cf609c81_a070_46f2_9543_e90c7ce5195b_ctl00_btnSearch"]' ).click()

        return ret

    def is_single_page( self ):
        r = self.result_indexes()
        return r['total'] <= 10


    def curr_page_num( self ):
        if self.is_single_page():
            return 1

        return int( self.driver.find_element_by_xpath( '//*[@id="ctl00_m_g_cf609c81_a070_46f2_9543_e90c7ce5195b_ctl00_grvMichrazim"]/tbody/tr[%d]/td/div/div/div[3]/span' % (self.num_of_rows() + 2) ).text )

    def num_of_rows( self ):

        if self.is_single_page():
            d = 1
        else:
            d = 2

        # one row for the heading, one for the page nums
        return len(self.driver.find_elements_by_xpath( '//*[@id="ctl00_m_g_cf609c81_a070_46f2_9543_e90c7ce5195b_ctl00_grvMichrazim"]/tbody/tr' )) - d

    def go_to_page_num( self, page_num ):

        while self.curr_page_num() != page_num:

            next_pages = self.get_next_pages()

            distances = [abs(page_num - page['page_num']) for page in next_pages]

            closest = distances.index( min(distances) )
            expected_page = next_pages[closest]['page_num']

            print 'on the way to page %d going to page %d' % ( page_num, expected_page )

            if next_pages[closest]['page_num'] < self.curr_page_num():
                raise AssertionError()

            next_pages[closest]['elem'].click()
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
        for i, e in enumerate( self.driver.find_elements_by_xpath( '//*[@id="ctl00_m_g_cf609c81_a070_46f2_9543_e90c7ce5195b_ctl00_grvMichrazim"]/tbody/tr[1]/th' ) ):
            hebrew_title = e.text
            if hebrew_title not in self.heading_name_map:
                raise AssertionError( 'unknown heading %s' % repr(hebrew_title) )
            title = self.heading_name_map[hebrew_title]
            if self.heading_order.index( title ) != i:
                raise AssertionError( 'heading %s expected at index %d but is at index %d' % (title, self.heading_order.index( title ), i) )

        print 'wasted %f secs on heading validation' % (time.time() - start_time )

    def extract_page_data( self ):

        start_time = time.time()

        #self.validate_headings()

        ret = []

        for row_i in xrange(self.num_of_rows()):
            data_elems = self.driver.find_elements_by_xpath( '//*[@id="ctl00_m_g_cf609c81_a070_46f2_9543_e90c7ce5195b_ctl00_grvMichrazim"]/tbody/tr[%d]/td' % (row_i+2) )
            if len(data_elems) != 8:
                raise AssertionError()

            if len(data_elems) != len(self.heading_order):
                raise AssertionError( 'wrong number of elems in row' )

            row = {}
            for i, heading in enumerate(self.heading_order):
                row[heading] = data_elems[i].text

            row['url'] = self.driver.find_element_by_xpath( '//*[@id="ctl00_m_g_cf609c81_a070_46f2_9543_e90c7ce5195b_ctl00_grvMichrazim"]/tbody/tr[%d]/td[1]/a' % (row_i+2) ).get_attribute('href')

            ret.append( row )

        print 'parsed page in %f secs' % (time.time() - start_time)

        return ret

    def parse( self ):

        if self.is_first_response():
            print "unsearched"
            self.requested_pages = [1]
            self.search()

        print self.result_indexes()


        self.extract_page_data()



# post processing
def add_publication_id( record ):
    if 'publication_id' in record:
        return

    url = record['url']
    publication_id = None

    for k,v in [x.split('=',1) for x in url.split('?',1)[1].split('&')]:
        if k == 'pID':
            publication_id = int(v)
            break

    if publication_id is None:
        raise AssertionError( 'pID not in url %s' % url )

    record['publication_id'] = publication_id

def split_subjects( record ):
    if type(record['subjects']) is list:
        return

    record['subjects'] = record['subjects'].split( '; ' )

def iter_records( filename ):
    for line in open( filename, 'r' ).xreadlines():
        data = json.loads(line)
        yield data

def remove_test_fields( record ):
    for f in ['documents', 'contact_email', 'contact', 'supplier_id', 'description', 'claim_date']:
        if f in record:
            record.pop( f )


def post_process_record( record ):
    add_publication_id( record )
    split_subjects( record )
    field_to_int( record, 'volume' )
    zero_is_none( record, 'volume' )


def post_processing( input, output, creation_date ):

    print "post processing %s into %s..." % (input, output)

    processed_file = open( output, 'w' )

    for record in iter_records(input):
        post_process_record( record )
        add_history_field( record, creation_date )
        remove_test_fields( record )
        processed_file.write( json.dumps(record) + '\n' )

    processed_file.close()

def get_num_of_publishers():
    for i in xrange(5):
        try:
            return search_web_page().num_of_options('publisher')
        except (selenium.common.exceptions.NoSuchElementException, selenium.common.exceptions.TimeoutException):
            if i == 4:
                raise

def scrape_data( base_path, scraper_class=publisher_scraper, **d ):
    num_of_publishers = get_num_of_publishers()
    for i in xrange( 1, num_of_publishers ):
        scraper_class( publisher_index=i, base_path=os.path.join(base_path, 'publisher'), **d ).scrape()

def stitch_scrape( base_path ):
    raw_data_file = open( os.path.join(base_path, 'raw_data.json'), 'w' )

    publisher_indexes = [int(x) for x in os.listdir( os.path.join(base_path, 'publisher') )]

    for i in publisher_indexes:
        p = publisher_scraper( publisher_index=i, base_path=os.path.join(base_path, 'publisher') )
        if os.path.exists( p.json_filename() ):
            print "reading data from %d..." % i
            raw_data_file.write( p.json_file('r').read() )
    raw_data_file.close()

class text_table:
    def __init__( self, column_count=None ):
        self.rows = []

    def add_row( self, row ):
        self.rows.append([str(c) for c in row])

    def __str__( self ):
        ret = ""

        lengths = []
        for i in xrange( len(self.rows[0]) ):
            lengths.append( max([len(r[i]) for r in self.rows]) )

        for ri,r in enumerate(self.rows):
            s = ""

            for i, c in enumerate(r):
                s += c + ( " " * (lengths[i] - len(c)) ) + (" " * 2)

            ret += s + "\n"

        return ret


def show_stats( base_path ):
    publisher_indexes = [int(x) for x in os.listdir( os.path.join(base_path, 'publisher') )]

    t = text_table()
    t.add_row( ['#', 'pages', 'exceptions', 'total_time', 'avg time'] )
    totals = {'pages':0, 'exceptions':0, 'time':0, 'avg_time':None}
    for i in sorted(publisher_indexes,key=lambda x:int(x)):
        p = publisher_scraper( publisher_index=i, base_path=os.path.join(base_path, 'publisher') )

        totals['pages'] += p.state['pages_scraped']
        totals['exceptions'] += p.state['exceptions']
        totals['time'] += p.state['work_time']

        if p.state['pages_scraped'] < 3:
            continue

        if 'exceptions' in p.state:
            if p.state['pages_scraped'] > 0:
                avg = '%.2f' % (p.state['work_time'] / p.state['pages_scraped'])
            else:
                avg = '-'
            t.add_row( [i, p.state['pages_scraped'], p.state['exceptions'], '%.2f' % p.state['work_time'], avg] )

    t.add_row( ['-', totals['pages'], totals['exceptions'], '%.2f' % totals['time'], '%.2f' % (totals['time'] / totals['pages'])] )
    print t


if __name__ == "__main__":
    from optparse import OptionParser

    parser = OptionParser( usage='usage: %prog [options] base_path' )
    parser.add_option("--scrape", dest="scrape", action='store_true', default=False)
    parser.add_option("--stitch", dest="stitch", action='store_true', default=False)
    parser.add_option("--post",   dest="post", action='store_true', default=False)
    parser.add_option("--update", dest="update", action='store_true', default=False)
    parser.add_option("--update-src", dest="update_src", action='store_true', default=False)
    parser.add_option("--date",   dest="date", action='store', default=None )
    parser.add_option("--stats",  dest="stats", action='store_true', default=False)
    parser.add_option("-v", "--verbose", dest="verbose", action='store_true', default=False)

    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.error( 'must provide a base path' )

    base_path = args[0]

    start_time = time.localtime()
    date_str = options.date or ('%d/%d/%d' % (start_time.tm_mday, start_time.tm_mon, start_time.tm_year))
    if options.scrape:
        scrape_data( base_path )

    if options.stitch or options.scrape:
        stitch_scrape( base_path )

    if options.post or options.scrape:
        post_processing( input=os.path.join(base_path, 'raw_data.json'), output=os.path.join(base_path, 'processed.json'), creation_date=date_str )

    if options.update:

        # we skip the supplier name because the updated data might already have a longer name from the extended data
        update_data( new_data_filename=os.path.join(base_path, 'processed.json'), diff_date=date_str, skip_fields=['supplier'], verbose=options.verbose )
        #exemption_json_to_csv( options.update, options.update + ".csv" )

    if options.stats:
        show_stats( base_path )
