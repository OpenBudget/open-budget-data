import sqlite3
import json
import logging
import time
import os
import sys
import hashlib
import gzip


class db_to_jsons(object):

    def process(self,input,output):

        if input.endswith('.updated'):
            input = input.replace('.updated','')
            
        conn = sqlite3.connect(input)
        c = conn.cursor()
        values = c.execute("""SELECT value from data""").fetchall()

        file(output,'w').write('\n'.join(v[0] for v in values))
        conn.close()

if __name__ == "__main__":
    input = sys.argv[1]
    output = sys.argv[2]
    key_fields = sys.argv[3:]
    processor = db_to_jsons().process(input,output,key_fields)
