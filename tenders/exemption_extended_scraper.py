#!/usr/bin/python
import base_scraper
import time
import pprint
import json
import os
import copy
import shutil
import requesocks as requests
from scrapy.selector import Selector
from post_processing import field_to_int, zero_is_none, iter_records, empty_str_is_none
from exemption_record import exemption_json_to_csv, update_data, exemption_record

class extended_data_scraper(base_scraper.base_scraper):
    def __init__( self, base_path ):
        base_scraper.base_scraper.__init__( self, base_path=base_path )

    def __repr__( self ):
        return 'extended_data_scraper()'

    def get_state( self ):
        self.web_page = extended_data_web_page()
        self.publication_ids = [r['publication_id'] for r in exemption_record.iter_records()]
        self.publication_ids.sort()
        return {'total_pages':len(self.publication_ids)}

    def go_to_page_num( self, page_num ):
        self.web_page.go_to_publication_id( self.publication_ids[page_num-1] )

    def extract_records( self ):
        return [self.web_page.extract_page_data()]

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
        self.response = self.session.request( 'get', url=url, timeout=10 )
        print 'loaded exended data in %f secs' % (time.time() - start_time)


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
            raise base_scraper.NoSuchElementException()

        if None in [ret["last_update_date"]]:
            raise base_scraper.NoSuchElementException()

        ret['url'] = self.url
        ret['documents'] = []
        links = sel.xpath('//*[@id="ctl00_PlaceHolderMain_pnl_Files"]/div/div/div[2]/a')
        update_times = sel.xpath('//*[@id="ctl00_PlaceHolderMain_pnl_Files"]/div/div/div[1]')

        if len(links) != len(update_times):
            raise AssertionError()

        for i in xrange( len(links) ):
            ret['documents'].append( {'description':links[i].xpath('text()')[0].extract(),
                                      'link':'http://www.mr.gov.il' + links[i].xpath('@href')[0].extract(),
                                      'update_time':update_times.xpath('text()')[0].extract()
                                      } )

        #print 'parsed exended data in %f secs' % (time.time() - start_time)

        return ret

# post processing
def format_documents_time( record ):
    for d in record['documents']:
        if isinstance(d['update_time'], str) or isinstance(d['update_time'], unicode):

            # "taarich idkoon mismach:   11:11 05/11/2014"

            time, date = d['update_time'].split(' ')[-2:]
            d['update_time'] = {'time':time, 'date':date}

def post_process_record( record ):
    empty_str_is_none( record, 'supplier_id' )
    field_to_int( record, 'supplier_id' )
    zero_is_none( record, 'supplier_id' )
    format_documents_time( record )

def post_processing( input, output ):

    print "post processing %s into %s..." % (input, output)

    processed_file = open( output, 'w' )

    for record in iter_records(input):
        post_process_record( record )
        processed_file.write( json.dumps(record) + '\n' )


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
    t = text_table()
    t.add_row( ['#', 'pages', 'exceptions', 'total_time', 'avg time'] )
    s = extended_data_scraper( base_path=base_path )

    if s.state['pages_scraped'] > 0:
        avg = '%.2f' % (s.state['work_time'] / s.state['pages_scraped'])
    else:
        avg = '-'
    t.add_row( [0, s.state['pages_scraped'], s.state['exceptions'], '%.2f' % s.state['work_time'], avg] )

    print t


if __name__ == "__main__":
    from optparse import OptionParser

    parser = OptionParser( usage='usage: %prog [options] base_path' )
    parser.add_option("--exemption-records", dest="exemption_records", metavar="json_filename", action="store", default=None)
    parser.add_option("--scrape", dest="scrape", action='store_true', default=False)
    parser.add_option("--post", dest="post", action='store_true', default=False)
    parser.add_option("--update", dest="update", action='store_true', default=False)
    parser.add_option("--date",   dest="date", action='store', default=None )
    parser.add_option("--stats",  dest="stats", action='store_true', default=False)
    parser.add_option("-v", "--verbose", dest="verbose", action='store_true', default=False)

    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.error( 'must provide a base path' )

    if options.exemption_records:
        exemption_record.db_filename = options.exemption_records

    base_path = args[0]

    start_time = time.localtime()
    date_str = options.date or ('%d/%d/%d' % (start_time.tm_mday, start_time.tm_mon, start_time.tm_year))
    if options.scrape:
        extended_data_scraper( base_path ).scrape()

    if options.post or options.scrape:
        post_processing( input=os.path.join(base_path, 'scraped.json'), output=os.path.join(base_path, 'processed.json') )

    if options.update:
        update_data( new_data_filename=os.path.join(base_path, 'processed.json'), diff_date=date_str, skip_fields=[], verbose=options.verbose )
        #exemption_json_to_csv( options.update, options.update + ".csv" )

    if options.stats:
        show_stats( base_path )#, options.exemption_records )
