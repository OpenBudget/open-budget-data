import sqlite3
import json
import logging
import time
import os
import sys
import hashlib
import gzip
import psycopg2
import datetime

def convert(val,typ):
    if typ=="date" and val is not None:
        if val.strip() != '':
            val = [int(x) for x in val.split('/')]
            val.reverse()
            val = datetime.date(*val)
        else:
            val = None
    return val

class dump_to_psql(object):

    def process(self,input,output,table,field_definitions):

        good_field_definitions = [(x[0].replace('/','_'),x[1]) for x in field_definitions]

        conn = psycopg2.connect('dbname=obudget')
        c = conn.cursor()
        c.execute("""DROP TABLE if exists %s;""" % table)
        c.execute("""CREATE TABLE %s
                     (%s);""" % (table,",".join("%s %s" % (x[0],x[1]) for x in good_field_definitions)))
        c.execute("""grant select ON %s to redash_reader;""" % table)

        if input.endswith('.gz'):
            infile = gzip.GzipFile(input)
        else:
            infile = file(input)
        to_insert = []
        for line in infile:
            line = line.strip()
            data = json.loads(line)
            values = [convert(data.get(field),typ) for field,typ in field_definitions]
            to_insert.append(values)
        c.executemany("""INSERT INTO %s VALUES(%s)""" % (table,",".join([r"%s"]*len(field_definitions))), to_insert)

        logging.debug("TABLE %s got %s records" % (table,len(to_insert)))

        conn.commit()

        for f in good_field_definitions:
            fieldname = f[0]
            c.execute("""create index {0}_{1}_idx_asc on {0}({1} asc);""".format(table,fieldname))
            c.execute("""create index {0}_{1}_idx_desc on {0}({1} desc);""".format(table,fieldname))

        conn.commit()
        conn.close()

        file(output,"w").write("OK")


if __name__ == "__main__":
    input = sys.argv[1]
    output = sys.argv[2]
    key_fields = sys.argv[3:]
    processor = dump_to_db().process(input,output,key_fields)
