import sqlite3
import json
import logging
import time
import os
import sys
import hashlib
import gzip
import psycopg2

class dump_to_psql(object):

    def process(self,input,output,table,field_definitions):

        conn = psycopg2.connect('dbname=obudget')
        c = conn.cursor()
        c.execute("""DROP TABLE %s if exists;""" % table)
        c.execute("""CREATE TABLE %s
                     (%s);""" % (table,",".join("%s %s" % x for x in field_definitions)))

        fields = dict(field_definitions)
        if input.endswith('.gz'):
            infile = gzip.GzipFile(input)
        else:
            infile = file(input)
        to_insert = []
        for line in infile:
            line = line.strip()
            data = json.loads(line)
            values = [data.get(field) for field,typ in field_definitions]
            to_insert.append(values)
        c.executemany("""INSERT INTO %s VALUES(%s)""" % (table,",".join(["?"]*len(field_definitions))), to_insert)
        os.utime(output, None)

        logging.debug("TABLE %s got %s records" % (table,len(to_insert)))

        conn.commit()
        conn.close()

if __name__ == "__main__":
    input = sys.argv[1]
    output = sys.argv[2]
    key_fields = sys.argv[3:]
    processor = dump_to_db().process(input,output,key_fields)
