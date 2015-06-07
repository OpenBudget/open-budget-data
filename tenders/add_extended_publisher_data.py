#!/usr/bin/python
import json
import csv
import sys
import os

class add_extended_publisher_data:
    def __init__( self ):

        # data from https://docs.google.com/spreadsheets/d/18IZ8KVdKIhyCeHHsJdAFxDScTReq4csw2LMXLYVBJZA/edit?usp=sharing
        
        self.publisher_extended_data = {}
        
        curr_path = os.path.split( __file__ ) [0]
        data = csv.reader( open(os.path.join(curr_path, 'extended_publisher_data.csv'), 'r') )
        
        heading = data.next()
        
        for row in data:
            if len(row) > len(heading):
                row = row[:len(heading)]
            if len(row) < len(heading):
                row += [''] * (len(heading) - len(row))

            row = [x.decode('utf8') for x in row]

            row = dict( zip(heading, row) )

            if len(row['publisher'].strip()) == 0:
                continue

            publisher = row.pop( 'publisher' )

            if 'logo' in row:
                row.pop( 'logo' )

            self.publisher_extended_data[publisher] = row
            

    def add( self, src_json_filename, dst_json_filename ):
        in_f = open(src_json_filename, 'r')
        out_f = open(dst_json_filename, 'w')

        for l in in_f.xreadlines():
            rec = json.loads( l )
            
            rec.update( self.publisher_extended_data.get( rec['publisher'], {} ) )

            out_f.write( json.dumps(rec) + '\n' )

        in_f.close()
        out_f.close()


def main():
    a = add_extended_publisher_data()
    a.add( sys.argv[1], sys.argv[2] )

if __name__ == "__main__":
    main()

