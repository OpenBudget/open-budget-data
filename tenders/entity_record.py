#!/usr/bin/python

import json
import time
import base_record
import csv
import sys
import copy

# TODO: support multiple id types: company, business, person id, ... each should have a separate id field and index, there should be a way to know the id type when creating a new record from an unknown id type

class entity_record(base_record.base_record):
    db_filename = 'db/entity.json'
    index_names = ['name', 'id']
    def __init__( self, record ):

        data = { 'id':None,
                 'names':[],
                 'exemptions':[] }

        data.update( record )

        base_record.base_record.__init__( self, data )

    def diff( self ):
        return True # will crash if a loaded entity record already exists, refer to base_record.base_record.load_records

    def exists( self ):
        if self['id'] is not None:
            return self.has_record( id=self['id'] )
        
        for name in self['names']:
            if self.has_record( name=name ):
                return True

        return False
        
    def index_record( self ):
        indexed = False

        for name in self['names']:
            if self.normalize_index(name) is not None:
                indexed = True
                self.add_index( 'name', name )

        if self.normalize_index(self['id']) is not None:
            indexed = True
            self.add_index( 'id', self['id'] )

        if not indexed:
            self.add_index( 'name', None )
            self.add_index( 'id', None )

    @base_record.connected_to_db
    def calculate_field( self, field_name ):
        from exemption_record import exemption_record

        if field_name == 'exemption_count':
            self['exemption_count'] = len(self['exemptions'])

        elif field_name == 'missing_volume_exemption_count':

            count = 0
            for publication_id in self['exemptions']:
                r = exemption_record.get_record( publication_id=publication_id )
                if (r['volume'] is None) or (r['volume'] == 0):
                    count += 1

            self['missing_volume_exemption_count'] = count

        elif field_name == 'exemption_volume':

            volume = 0
            for publication_id in self['exemptions']:
                r = exemption_record.get_record( publication_id=publication_id )
                volume += r['volume'] if r['volume'] is not None else 0

            self['exemption_volume'] = volume

        elif field_name == 'exemption_offices':
            from exemption_record import exemption_record

            ret = {}

            for publication_id in self['exemptions']:
                r = exemption_record.get_record( publication_id=publication_id )
                ret.setdefault( r['publisher'], [] )
                ret[r['publisher']].append( r )

            self['exemption_offices'] = ret

        elif field_name == 'exemption_offices_2014':
            from exemption_record import exemption_record

            ret = {}

            started_2014 = numerate_date( '1/1/2014' )

            for publication_id in self['exemptions']:
                r = exemption_record.get_record( publication_id=publication_id )

                if numerate_date(r['start_date']) < started_2014:
                    continue

                ret.setdefault( r['publisher'], [] )
                ret[r['publisher']].append( r )

            self['exemption_offices_2014'] = ret


        else:
            raise KeyError( 'unknown field %s' % field_name )

def csv_field( d ):
    if type(d) is unicode:
        d = d.encode('cp1255', 'ignore')

    if type(d) not in [str, unicode]:
        d = str(d)

    #return '"' + d.replace( '"', "'" ) + '"'
    return d

def csv_line( l ):
    return [csv_field(x) for x in l]

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

def date_str( n ):
    t = time.localtime( n )
    return '%d/%d/%d' % (t.tm_mday, t.tm_mon, t.tm_year)


def entity_json_to_csv( csv_filename, verbose=False ):

    print "generating csv %s from json file %s..." % (csv_filename, entity_record.db_filename)

    csv_file = open(csv_filename, 'wb')
    csv_writer = csv.writer( csv_file )
    
    headings = ["id"]

    max_names = 0
    for data in entity_record.iter_records():
        max_names = max([max_names, len(data['names'])])

    for i in xrange(max_names):
        headings.append( 'name.%d' % i )

    headings.extend( ['exemption_count', 'exemption_volume'] )

    csv_writer.writerow( csv_line(headings) )

    for data_i, data in enumerate( entity_record.iter_records() ):
        
        #if data_i > 10:
        #    break

        if verbose:
            if data_i > 0 and data_i % 100 == 0:
                sys.stdout.write( '\r%d/%d' % (data_i, entity_record.records_count()) )
                sys.stdout.flush()

        # if headings is None:
        #     headings = data.keys()
        #     csv_writer.writerow( csv_line(headings) )

        curr_data = []
        for k in headings:
            if k.split('.')[0] == 'name':
                i = int(k.split('.')[1])
                if i < len(data['names']):
                    curr_data.append( data['names'][i] )
                else:
                    curr_data.append( '' )
            else:
                curr_data.append( data[k] )
        
        csv_writer.writerow( csv_line(curr_data) )

    if verbose:
        print '\r%d/%d' % (entity_record.records_count(), entity_record.records_count())

    csv_file.close()

if __name__ == "__main__":
    from optparse import OptionParser

    parser = OptionParser( usage='usage: %prog [options]' )
    parser.add_option("--db-filename", dest="db_filename", action='store', metavar="filename", default=None)
    parser.add_option("--to-csv", dest="to_csv", action='store', metavar="output_filename", default=None)
    parser.add_option("-v", "--verbose", dest="verbose", action='store_true', default=False)

    (options, args) = parser.parse_args()

    if options.db_filename is not None:
        entity_record.db_filename = options.db_filename

    if options.to_csv:
        entity_json_to_csv( options.to_csv, verbose=options.verbose )

