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
            if rec.get('net_revised',rec.get('net_allocated',0)) <= 0:
                continue
            recs[rec['code']] = {
                'code':rec['code'],
                'size':rec['net_revised'],
                'name':rec['title'],
                'orig_size':rec['net_allocated']
            }

        keys = recs.keys()
        keys.sort(key=lambda x:int("1"+x))
        for key in keys:
            print key, recs[key]
            if root is None:
                root = recs[key]
            else:
                node = root
                while len(key) > len(node['code'])+2:
                    for child in node['children']:
                        if key.startswith(child['code']):
                            node = child
                            break
                    else:
                        print "ERR ERR ERR ",key,node
                node.setdefault('children',[]).append(recs[key])
                if node.has_key('size'):
                    del node['size']

        out = {'key':'static-budget','value':root}
        file(output,'w').write(json.dumps(out))

if __name__=="__main__":
    extract_for_partition_layout().process(sys.argv[1],sys.argv[2],int(sys.argv[3]))
