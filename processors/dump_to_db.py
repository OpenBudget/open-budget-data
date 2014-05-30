import sqlite3
import json
import logging
import time
import os
import sys
import hashlib
import gzip

if __name__ == "__main__":
    key_fields = sys.argv[1]
    inputs = sys.argv[2:-1]
    output = sys.argv[-1]
    processor = dump_to_db().process(inputs,output,key_fields)

class dump_to_db(object):

    def process(self,input,output,key_fields):

        conn = sqlite3.connect(output)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS data
                     (timestamp real, key text primary key, value text, dirty smallint, remote_key text )""")
        c.execute("""CREATE UNIQUE INDEX IF NOT EXISTS data_idx ON data(key)""")


        to_insert = []
        to_update = []
        if input.endswith('.gz'):
            infile = gzip.GzipFile(input)
        else:
            infile = file(input)
        for line in infile:
            line = line.strip()
            data = json.loads(line)
            key = "/".join("%s:%s" % (field,data[field]) for field in key_fields)
            #key = hashlib.md5(key.encode('utf8')).hexdigest()
            current = c.execute("""SELECT value from data where key=?""",(key,)).fetchone()
            if current is None:
                to_insert.append( (time.time(), key, line, 1, None) )
            else:
                if current[0] != line:
                    to_update.append( (time.time(), line, 1, key))
        if len(to_insert)>0:
            c.executemany("""INSERT OR REPLACE INTO data VALUES(?,?,?,?,?)""", to_insert)
        if len(to_update)>0:
            c.executemany("""UPDATE data SET timestamp=?,value=?,dirty=? WHERE key=?""", to_update)

        os.utime(output, None)

        logging.debug("Added %s records" % len(to_insert))
        logging.debug("Modified %s records" % len(to_update))

        conn.commit()
        conn.close()
