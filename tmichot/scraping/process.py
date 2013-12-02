import csv
import json
import sys

strings = {}
string_id = 0
def _string_id(s):
    global strings, string_id
    if s in strings:
        return strings[s]
    else:
        string_id = string_id + 1
        strings[s] = string_id
        return string_id

def get_strings():
    global strings
    return dict((int(v),k) for k,v in strings.iteritems())
    
if __name__=="__main__":
    reader = csv.reader(file("tmichot.csv"))
    out = {}
    for line in reader:
        try:
            year, _, office, tak_id, recepient, sup_type, tak_name, sup_num, app_budget, used_budget = line
        except:
            print line
            print len(line)
            sys.exit(1)
        value = { 'o':_string_id(office), 'i':tak_id, 'n':_string_id(tak_name), 'r':_string_id(recepient), 'v':{}}
        key = "/".join(str(value[x]) for x in 'orin')
        out.setdefault(key,value)['v'][int(year)] = {'n':int(sup_num), 'a':int(app_budget), 'u':int(used_budget)}
        #out.append([int(year), _string_id(office), tak_id, _string_id(tak_name), _string_id(recepient), int(sup_num), int(app_budget), int(used_budget)])
    file("out.js","w").write("data="+json.dumps(out.values())+';\nstrings='+json.dumps(get_strings())+";")
    file("out.json","w").write(json.dumps({"tmichot":out.values(),"strings":get_strings()}))
        
