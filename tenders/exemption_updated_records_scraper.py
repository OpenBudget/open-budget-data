#!/usr/bin/python
import base_scraper
import exemption_tables_scraper
import exemption_extended_scraper
from exemption_record import numerate_date, date_str, update_data, exemption_record
from entity_record import entity_record
from post_processing import field_to_int, zero_is_none, iter_records, add_history_field
import os
import time
import json
from datetime import datetime, timedelta

# scraper
class publisher_updated_scraper(exemption_tables_scraper.publisher_scraper):

    def __init__( self, updated_since, *p, **d ):

        if updated_since == 'yesterday':
            yesterday = datetime.now() - timedelta(days=2)
            updated_since = yesterday.strftime('%d/%m/%y')

        if updated_since == 'last_week':
            yesterday = datetime.now() - timedelta(days=8)
            updated_since = yesterday.strftime('%d/%m/%y')

        self.scrape_updated_since = numerate_date( updated_since )

        exemption_tables_scraper.publisher_scraper.__init__( self, *p, **d )

    def __repr__( self ):
        return 'publisher_updated_scraper( %d, %s )' % (self.publisher_index, date_str(self.scrape_updated_since))

    def get_state( self ):

        state = exemption_tables_scraper.publisher_scraper.get_state( self )

        self.extended_web_page = exemption_extended_scraper.extended_data_web_page()

        state['done'] = False

        return state


    def need_scraping( self ):

        if not exemption_tables_scraper.publisher_scraper.need_scraping( self ):
            return False

        if 'done' in self.state:
            if self.state['done']:
                return False

        return exemption_tables_scraper.publisher_scraper.need_scraping( self )


    def extract_records( self ):

        records = self.web_page.extract_page_data()

        ret = []

        for record in records:

            self.extended_web_page.go_to_url( record['url'] )

            extended_data = self.extended_web_page.extract_page_data()

            record.update( extended_data )

            if numerate_date(record['last_update_date']) < self.scrape_updated_since:
                self.state['done'] = True
                break

            ret.append( record )

        return ret


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
    t.add_row( ['#', 'total_pages', 'pages', 'exceptions', 'total_time', 'avg time'] )
    totals = {'pages':0, 'exceptions':0, 'time':0, 'avg_time':None}
    for i in sorted(publisher_indexes,key=lambda x:int(x)):
        p = publisher_updated_scraper( publisher_index=i, base_path=os.path.join(base_path, 'publisher'), updated_since='-' )

        totals['pages'] += p.state['pages_scraped']
        totals['exceptions'] += p.state['exceptions']
        totals['time'] += p.state['work_time']

        #if p.state['pages_scraped'] < 3:
        #    continue

        if p.state['pages_scraped'] > 0:
            avg = '%.2f' % (p.state['work_time'] / p.state['pages_scraped'])
        else:
            avg = '-'
        t.add_row( [i, p.state['total_pages'], p.state['pages_scraped'], p.state['exceptions'], '%.2f' % p.state['work_time'], avg] )

    t.add_row( ['-', '-', totals['pages'], totals['exceptions'], '%.2f' % totals['time'], '%.2f' % (totals['time'] / totals['pages'])] )
    print t

def post_processing( input, output, creation_date ):

    print "post processing %s into %s..." % (input, output)

    processed_file = open( output, 'w' )
    
    for record in iter_records(input):
        add_history_field( record, creation_date )
        exemption_tables_scraper.post_process_record( record )
        exemption_extended_scraper.post_process_record( record )

        processed_file.write( json.dumps(record) + '\n' )

    processed_file.close()

if __name__ == "__main__":
    from optparse import OptionParser

    parser = OptionParser( usage='usage: %prog [options] base_path' )
    parser.add_option("--scrape", dest="scrape", action='store', metavar='since', default=None)
    parser.add_option("--exemption-records", dest="exemption_records", metavar="json_filename", action="store", default=None)
    parser.add_option("--entity-records", dest="entity_records", metavar="json_filename", action="store", default=None)
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

    if options.exemption_records:
        exemption_record.db_filename = options.exemption_records

    if options.entity_records:
        entity_record.db_filename = options.entity_records

    base_path = args[0]

    start_time = time.localtime()
    options.date = options.date or ('%d/%d/%d' % (start_time.tm_mday, start_time.tm_mon, start_time.tm_year))
    if options.scrape:
        exemption_tables_scraper.scrape_data( base_path, scraper_class=publisher_updated_scraper, updated_since=options.scrape )

    if options.stitch or options.scrape:
        exemption_tables_scraper.stitch_scrape( base_path )

    if options.post or options.scrape:
        post_processing( input=os.path.join(base_path, 'raw_data.json'), output=os.path.join(base_path, 'processed.json'), creation_date=options.date )

    if options.update:
        update_data( new_data_filename=os.path.join(base_path, 'processed.json'), diff_date=options.date, skip_fields=[], verbose=options.verbose )
        #exemption_json_to_csv( options.update, options.update + ".csv" )

    if options.stats:
        show_stats( base_path )
