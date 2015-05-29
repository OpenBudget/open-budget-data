import sqlite3
import json
import logging
import time
import os
import sys
import hashlib
import gzip


class dump_to_db(object):

    def process(self,input,output,key_fields,model,process_history=True):

        conn = sqlite3.connect(output)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS data
                     (timestamp real, key text primary key, value text, dirty smallint, remote_key text )""")
        c.execute("""CREATE UNIQUE INDEX IF NOT EXISTS data_idx ON data(key)""")


        history = []
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
            history_key = { field:data[field] for field in key_fields }
            #key = hashlib.md5(key.encode('utf8')).hexdigest()
            current = c.execute("""SELECT value from data where key=?""",(key,)).fetchone()
            if current is None:
                if process_history:
                    history.append({
                        'model': model,
                        'selector': history_key,
                        'time' : time.time(),
                        'created': True
                    })
                    if data.has_key('history'):
                        for h in history:
                            try:
                                date = time.mktime(time.strptime(h['date'],"%d/%m/%Y"))
                                if h['field'] == 'creation':
                                    history.append({
                                        'model': model,
                                        'selector': history_key,
                                        'time' : date,
                                        'created': True,
                                    })
                                else:
                                    history.append({
                                        'model': model,
                                        'selector': history_key,
                                        'time' : date,
                                        'field': h['field'],
                                        'from' : h['from'],
                                        'to'   : h['to'],
                                        'created': False
                                    })
                            except Exception, e:
                                logging.warn("%s/%s: Failed to parse history item %r (%r)" % (model,key,h,e) )
                                pass
                        del data['history']
                        line = json.dumps(data, sort_keys=True)
                to_insert.append( (time.time(), key, line, 1, None) )
            else:
                if current[0] != line:
                    if process_history:
                        current = json.loads(current[0])
                        for k,v in data.iteritems():
                            if current.get(k) != v:
                                history.append({
                                    'model': model,
                                    'selector': history_key,
                                    'field': k,
                                    'from' : current.get(k),
                                    'to'   : v,
                                    'time' : time.time(),
                                    'created': False
                                })
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

        change_history = file('change_history.jsons','a')
        for h in history:
            change_history.write(json.dumps(h,sort_keys=True)+'\n')

if __name__ == "__main__":
    input = sys.argv[1]
    output = sys.argv[2]
    key_fields = sys.argv[3:]
    processor = dump_to_db().process(input,output,key_fields)
