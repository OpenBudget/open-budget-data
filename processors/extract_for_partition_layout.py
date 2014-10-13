import sys
import json

class extract_for_partition_layout(object):

    def process(self,input,output,year=2014):

        root = None
        recs = {}

        for line in file(input):
            rec = json.loads(line)
            if rec['year'] != year:
                continue
            if len(rec['code']) > 10:
                continue
            if rec['code'].startswith('0000'):
                continue
            revised = rec.get('net_revised',0)
            if revised <= 0:
                if len(rec['code'])>8:
                    try:
                        parent = recs[rec['code'][:-2]]
                        revised = int(rec['net_allocated'] * 1.0 * parent['s'] / parent['o'])
                    except:
                        continue
                else:
                    continue

            recs[rec['code']] = {
                'c':rec['code'],
                's':revised,
                'n':rec['title'],
                'o':rec['net_allocated']
            }

        keys = recs.keys()
        keys.sort(key=lambda x:int("1"+x))
        for key in keys:
            if root is None:
                root = recs[key]
            else:
                node = root
                while len(key) > len(node['c'])+2:
                    for child in node['k']:
                        if key.startswith(child['c']):
                            node = child
                            break
                    else:
                        print "ERR ERR ERR ",key
                        node = None
                        break
                if node is not None:
                    node.setdefault('k',[]).append(recs[key])
                    if node.has_key('s'):
                        del node['s']

        out = {'key':'static-budget','value':root}
        file(output,'w').write(json.dumps(out,separators=(',', ':')))

if __name__=="__main__":
    extract_for_partition_layout().process(sys.argv[1],sys.argv[2],int(sys.argv[3]))
