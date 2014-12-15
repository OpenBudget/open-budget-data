#!/usr/bin/python
import json
import time
import sys
import base_record
import csv

class exemption_record(base_record.base_record):
    db_filename = 'db/exemption.json'
    all_subjects = []
    no_diff_fields = ['history']
    index_names = ['publication_id']
    def __init__( self, record ):
        base_record.base_record.__init__( self, record )

    def has_updated_since( self, since_date ):
        for h in self['history']:
            curr_date = h['date']
            if curr_date == '-':
                continue
            if numerate_date(curr_date) >= numerate_date(since_date):
                return True
        return False

    @base_record.connected_to_db
    def calculate_field( self, field_name ):
        if field_name.split('.',1)[0] == 'entity':
            
            # TODO: remove this
            if 'supplier_id' not in self:
                self[field_name] = "-"
                return

            self[field_name] = self.get_entity()[field_name.split('.',1)[1]]

        else:
            raise KeyError( 'unknown field %s' % field_name )

    @base_record.connected_to_db
    def index_record( self ):
        self.add_index( 'publication_id', self['publication_id'] )

    @base_record.connected_to_db
    def exists( self ):
        return self.has_record( publication_id=self['publication_id'] )

    @base_record.connected_to_db
    def add_to_db( self ):
        base_record.base_record.add_to_db( self )
        for s in self['subjects']:
            if s not in self.all_subjects:
                self.all_subjects.append( s )

    @base_record.connected_to_db
    def diff( self, diff_date=None, skip_fields=[] ):
        ret = []
        
        base = self.get_record( publication_id=self['publication_id'] )

        for k in self.data:
            if k in self.no_diff_fields + skip_fields:
                continue
            if k in base:
                if self[k] != base[k]:

                    # don't replace not-none fields with none
                    if (base[k] is not None) and (self[k] is None):
                        continue

                    ret.append( {'date':diff_date, 'field':k, 'from':base[k], 'to':self[k]} )

        return ret

    @base_record.connected_to_db
    def save_diff( self, diff_date, skip_fields=[] ):
        base = self.get_record( publication_id=self['publication_id'] )
        base['history'].extend( self.diff(diff_date, skip_fields) )

        for k in self.data:
            if k in self.no_diff_fields + skip_fields:
                continue

            if k in base:
                if self[k] != base[k]:

                    # don't replace not-none fields with none
                    if (base[k] is not None) and (self[k] is None):
                        continue

            base.set_data_field( k, self[k] )

    def get_entity( self ):
        from entity_record import entity_record

        if self['supplier_id'] is not None:
            if entity_record.has_record( id=self['supplier_id'] ):
                return entity_record.get_record( id=self['supplier_id'] )

        if entity_record.has_record( name=self['supplier'] ):
            return entity_record.get_record( name=self['supplier'] )

        raise IndexError( 'no entity record found for exemption %d' % self['publication_id'] )

    def update_entity( self ):
        from entity_record import entity_record

        # TODO: remove this
        if 'supplier_id' not in self:
            return

        try:
            entity = self.get_entity()
        except IndexError:
            entity = None

        if entity is None:
            entity = entity_record( dict(id=self['supplier_id'],
                                         names=[self['supplier']]) )
            entity.add_to_db()
        
        if self['publication_id'] not in entity['exemptions']:
            entity['exemptions'].append( self['publication_id'] )



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
    if d == '-':
        return None
    if type(d) in [int, long, float]:
        return d
    day, month, year = [int(x) for x in d.split('/')]
    return time.mktime( time.struct_time([year, month, day, 0, 0, 0, 0, 0, 0]) )

def date_str( n ):
    if n is None:
        return "-"
    t = time.localtime( n )
    return '%d/%d/%d' % (t.tm_mday, t.tm_mon, t.tm_year)


def exemption_json_to_csv( csv_filename, write_subjects=False, write_documents=False, verbose=False ):

    print "generating csv %s from json file %s..." % (csv_filename, exemption_record.db_filename)

    csv_file = open(csv_filename, 'w')
    csv_writer = csv.writer( csv_file )
    
    headings = ["publication_id", "publisher", "contact", "contact_email", "supplier", "supplier_id", 'entity.exemption_count', 'entity.exemption_volume', "description", "volume", "start_date", "end_date", "claim_date", "decision", "regulation", "url", "last_update_date", "last_recorded_update_date"]

    if write_documents:
        max_documents = 0
        for data in exemption_record.iter_records():
            if 'documents' in data:
                max_documents = max([max_documents, len(data['documents'])])

        for i in xrange(max_documents):
            headings.append( 'document.%d.description' % i )
            headings.append( 'document.%d.link' % i )

        for s in exemption_record.all_subjects:
            headings.append( 'subject.%s' % s )

    csv_writer.writerow( csv_line(headings) )

    for data_i, data in enumerate( exemption_record.iter_records() ):
        
        #if data_i > 10:
        #    break

        if verbose:
            if data_i > 0 and data_i % 100 == 0:
                sys.stdout.write( '\r%d/%d' % (data_i, exemption_record.records_count()) )
                sys.stdout.flush()

        # if headings is None:
        #     headings = data.keys()
        #     csv_writer.writerow( csv_line(headings) )

        curr_data = []
        for k in headings:
            if k.split('.')[0] == 'document':
                if 'documents' not in data:
                    curr_data.append( '' )
                else:                    
                    i, k = k.split('.',2)[1:]
                    i = int(i)
                    if i < len(data['documents']):
                        curr_data.append( data['documents'][i][k] )
                    else:
                        curr_data.append( '' )
            elif k.split('.')[0] == 'subject':
                s = k.split('.',1)[1]
                if s in data['subjects']:
                    curr_data.append( True )
                else:
                    curr_data.append( False )
            elif k == 'last_recorded_update_date':
                curr_data.append( date_str( max( [numerate_date(x['date']) for x in data['history']] ) ) )
            elif k.split('.')[0] == 'entity':
                curr_data.append( data[k] )
            elif k in data:
                curr_data.append( data[k] )
            else:
                curr_data.append( '-' )
        
        csv_writer.writerow( csv_line(curr_data) )

    if verbose:
        print '\r%d/%d' % (exemption_record.records_count(), exemption_record.records_count())
    csv_file.close()

def update_data( new_data_filename, diff_date, skip_fields, verbose=False ):

    from entity_record import entity_record
    print "updating with new data from %s..." % (new_data_filename)
    
    for data_i, record in enumerate( base_record.iter_json_records( new_data_filename ) ):

        if verbose:
            if data_i > 0 and data_i % 100 == 0:
                sys.stdout.write( '\r%d' % (data_i) )
                sys.stdout.flush()

        record = exemption_record(record)

        if record.exists():
            record.save_diff( diff_date, skip_fields=skip_fields )
        else:
            record.add_to_db()
            
        record.update_entity()

        # if record['publication_id'] == 12664:
        #     print 
        #     print record.normalize_data( record['supplier']  )
        #     print record
        #     print record.get_entity()

    if verbose:
        print '\r%d' % (data_i)

    exemption_record.write_records()
    entity_record.write_records()

def update_entities():

    from entity_record import entity_record
    for record in exemption_record.iter_records():

        record = exemption_record(record)
        record.update_entity()

        if record['publication_id'] == 12664:
            print record.get_entity()

    entity_record.write_records()


if __name__ == "__main__":
    from optparse import OptionParser

    parser = OptionParser( usage='usage: %prog [options]' )
    parser.add_option("--db-filename", dest="db_filename", action='store', metavar="filename", default=None)
    parser.add_option("--to-csv", dest="to_csv", action='store', metavar="output_filename", default=None)
    parser.add_option("--csv-subjects", dest="csv_subjects", action='store_true', default=False)
    parser.add_option("--csv-documents", dest="csv_documents", action='store_true', default=False)
    parser.add_option("-v", "--verbose", dest="verbose", action='store_true', default=False)
    parser.add_option("--update-entities", dest="update_entities", action='store_true', default=False)

    (options, args) = parser.parse_args()

    if options.db_filename is not None:
        exemption_record.db_filename = options.db_filename

    if options.to_csv:
        exemption_json_to_csv( options.to_csv, write_subjects=options.csv_subjects, write_documents=options.csv_documents, verbose=options.verbose )

    if options.update_entities:
        update_entities()

