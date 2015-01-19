import time
import selenium.common.exceptions
import os
import json
import copy
import urllib3.exceptions
import requests.exceptions

def rec_mkdir( d ):
    s = d.split(os.path.sep)
    for i in xrange(len(s)):
        if s[i] == '':
            continue
        curr_dir = os.path.sep.join( s[:(i+1)] )
        if os.path.exists( curr_dir ):
            if not os.path.isdir(curr_dir):
                raise AssertionError()
            continue

        os.mkdir( curr_dir )
            
class scraping_state:
    def __init__( self, curr_base_path, default ):
        self.filename = os.path.join( curr_base_path, 'scraper.json' )
        self.default = default
        self.load()
    
    def load( self ):
        if not os.path.exists( self.filename ):
            self.data = copy.deepcopy( self.default )
            return

        self.data = json.load( open(self.filename, 'r') )

    def save( self ):
        json.dump( self.data, open( self.filename, 'w' ) )

    def __getitem__( self, k ):
        return self.data[k]

    def __setitem__( self, k, v ):
        self.data[k] = v

    def __contains__( self, k ):
        if self.data is None:
            return False
        return k in self.data

class NoSuchElementException(Exception):
    pass

class base_scraper:
    def __init__( self, base_path ):
        self.base_path = base_path

        rec_mkdir( self.base_path )

        self.read_state()

    def need_scraping( self ):
        if self.state.data is None:
            return True

        return self.state['pages_scraped'] < self.state['total_pages']

    def read_state( self, default=None ):
        self.state = scraping_state( self.base_path, default )

    def init_state( self ):
        for i in xrange(2):
            curr_state = self.get_state()

            if 'total_pages' not in curr_state:
                raise AssertionError( 'total_pages not in state' )

            curr_state['pages_scraped'] = 0
            curr_state['exceptions'] = 0
            curr_state['work_time'] = 0

            self.read_state( curr_state )

            for k in curr_state:
                if k in ['pages_scraped', 'exceptions', 'work_time']:
                    continue

                if curr_state[k] != self.state[k]:

                    # reset the scraper and try again
                    if i == 0:
                        self.reset_scraper()
                        curr_state = None
                        break
                    else:
                        raise ValueError( 'scraper %s state inconsistent %s is different %s != %s' % (repr(self), k, repr(curr_state[k]), repr(self.state[k])) )

            if curr_state is not None:
                break

        self.state.save()

    def json_filename( self ):
        return os.path.join(self.base_path, 'scraped.json')

    def json_file( self, mode ):
        return open( self.json_filename(), mode )

    def _scrape( self ):

        start_time = time.time()

        self.init_state()

        orig_work_time = self.state['work_time']
        
        self.curr_page = self.state['pages_scraped'] + 1
        
        self.scraped_records = 0

        while self.need_scraping() and (self.curr_page <= self.state['total_pages']):
            try:
                self.go_to_page_num( self.curr_page )
            except:
                self.state['work_time'] = orig_work_time + (time.time() - start_time)
                self.state['exceptions'] += 1
                self.state.save()
                raise
                

            try:
                data = ""
                for rec in self.extract_records():
                    self.scraped_records += 1
                    data += json.dumps(rec) + '\n'
            except:
                self.state['work_time'] = orig_work_time + (time.time() - start_time)
                self.state['exceptions'] += 1
                self.state.save()
                raise

            if data:
                f = self.json_file( 'a' )
                f.write( data )
                f.close()

            self.state['pages_scraped'] = self.curr_page
            self.state['work_time'] = orig_work_time + (time.time() - start_time)
            self.state.save()
            print time.asctime(), "scraped %s page %d/%d" % (repr(self), self.curr_page, self.state['total_pages'])

            self.curr_page += 1

        print "scraper %s completed" % repr(self)

    def scrape( self ):
        if not self.need_scraping():
            print "scraper %s completed" % repr(self)
            return

        prev_scraped_records = []
        self.scraped_records = 0

        while self.need_scraping:
            try:
                self._scrape()
                break
            except (selenium.common.exceptions.TimeoutException, urllib3.exceptions.ReadTimeoutError, requests.exceptions.ConnectionError, requests.exceptions.HTTPError, requests.exceptions.SSLError, requests.exceptions.Timeout), e:
                if 'web_page' in self.__dict__:
                    if 'driver' in self.web_page.__dict__:
                        self.web_page.driver.save_screenshot( os.path.join(self.base_path, 'timeout.png') )
                pass
            except (selenium.common.exceptions.NoSuchElementException, NoSuchElementException), e:
                prev_scraped_records.append( self.scraped_records )

                # if we get this exception 3 times with no records then this could be a bug and not a timeout
                if len(prev_scraped_records) >= 3:
                    if prev_scraped_records[:-3] == [0,0,0]:
                        if 'web_page' in self.__dict__:
                            if 'driver' in self.web_page.__dict__:
                                self.web_page.driver.save_screenshot( os.path.join(self.base_path, 'crash.%f.png' % time.time()) )
                        raise

            print time.asctime(), "timed out", str(e)
            time.sleep( 60 )


class rate_limiter:
    def __init__( self, rate_limit=None ):
        self.rate_limit_time = rate_limit
        self.last_access_time = None

    def rate_limit( self ):
        if self.rate_limit_time is None:
            return

        if self.last_access_time is None:
            self.last_access_time = time.time()
            return

        time_since_last = time.time() - self.last_access_time
        if time_since_last < self.rate_limit_time:
            sleep_time = self.rate_limit_time - time_since_last
            print "rate limit: sleeping %d secs" % sleep_time
            time.sleep( sleep_time )
            
        self.last_access_time = time.time()
    
