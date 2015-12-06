import logging
from datetime import datetime
import json

if __name__ == "__main__":
    input = sys.argv[1]
    output = sys.argv[2]
    processor = consolidate_change_dates().process(input,output)

KIND_SCORES = { 'approval' : 3,
                'approved-approx' : 1,
                'pending' : 2 }
KIND_TYPES = { 'approval' : 0,
               'approved-approx' : 1,
               'pending' : 10 }

class consolidate_change_dates(object):
    def process(self,input,output):
        dates = {}
        leading_items = {}
        out = file(output,"w")
        rows = [ json.loads(line.strip()) for line in file(input) ]
        rows.sort( key=lambda x: "%(year)d/%(leading_item)03d/%(req_code)03d" % x, reverse=True )

        # Find best date for each row
        for line in rows:
            leading_item = "%(year)s/%(leading_item)s" % line
            req_code = line['req_code']
            kind_score = -1
            date = None
            for k,v in line.iteritems():
                if not k.startswith('date/'):
                    continue
                _kind = k.split('/')[1]
                _score = KIND_SCORES[_kind]
                if _score > kind_score:
                    kind = KIND_TYPES[_kind]
                    kind_score = _score
                    vparts = [ int(x) for x in v.split('/') ]
                    date = datetime(year=vparts[2], month=vparts[1], day=vparts[0])
            if date is not None:
                leading_items.setdefault(leading_item,{})[req_code] = (date,kind)
            else:
                leading_items.setdefault(leading_item,{})[req_code] = (datetime.now(),10)

        # Fill in dates for missing rows
        for row in rows:
            leading_item = "%(year)s/%(leading_item)s" % row
            req_code = row['req_code']

            request_codes = leading_items.get(leading_item,{})
            request_codes = list( request_codes.iteritems() )
            request_codes.sort( key=lambda x:x[0] )

            mindate = datetime(year=row['year'], month=1, day=1)
            maxdate = datetime(year=row['year'], month=12, day=31)
            mincode = 0
            maxcode = None
            date = None
            kind = None
            for record in request_codes:
                rec_req_code, rec_date_kind = record
                rec_date, rec_kind = rec_date_kind
                if rec_req_code < req_code:
                    mindate = rec_date
                    mincode = rec_req_code
                if rec_req_code == req_code:
                    date = rec_date
                    kind = rec_kind
                    #print leading_item,"/",req_code,":",date
                    break
                if rec_req_code > req_code:
                    maxdate = rec_date
                    maxcode = rec_req_code
                    break
            if date is None:
                kind = KIND_TYPES['approved-approx']
                if maxcode is None:
                    date = maxdate
                else:
                    diff = maxcode - mincode
                    delta = maxdate - mindate
                    delta = (delta / diff) * (req_code - mincode)
                    date = mindate + delta
                leading_items.setdefault(leading_item,{})[req_code] = (date,kind)

        # prepare output
        for row in rows:
            leading_item = "%(year)s/%(leading_item)s" % row
            req_code = row['req_code']
            date,kind = leading_items[leading_item][req_code]
            to_del = [ k for k in row.keys() if k.startswith('date/')]
            for k in to_del:
                del row[k]
            row['date'] = date.strftime("%d/%m/%Y")
            row['date_type'] = kind

        # write output
        for row in rows:
            out.write(json.dumps(row)+'\n')
