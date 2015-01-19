import json

def add_history_field( record, date ):
    if 'history' in record:
        return

    record['history'] = [{'date':date, 'field':'creation'}]

def iter_records( filename ):
    for line in open( filename, 'r' ).xreadlines():
        data = json.loads(line)
        yield data

def field_to_int( record, field_name ):
    if type(record[field_name]) in [int, long, float]:
        return

    if record[field_name] is None:
        return None

    record[field_name] = record[field_name].replace(',','')
    if '.' in record[field_name]:
        record[field_name] = float(record[field_name])
    else:
        record[field_name] = long(record[field_name])

def zero_is_none( record, field_name ):
    if field_name in record:
        if record[field_name] == 0:
            record[field_name] = None

def empty_str_is_none( record, field_name ):
    if field_name in record:
        if type(record[field_name]) in [str,unicode]:
            if len(record[field_name].strip()) == 0:
                record[field_name] = None
