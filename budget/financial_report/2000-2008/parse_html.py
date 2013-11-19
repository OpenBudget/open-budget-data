### encoding: utf8

import sys
import re
import json
import urllib2

year_re = re.compile('31.12.([0-9]+)')
code_re = re.compile('[0-9][0-9]')
sep = '--------------------------------------------------------------------------------------------------------------------------------'

def parse_number(s):
    neg = '-' in s
    num = s.replace(',','').replace('-','')
    num = int(float(num)/1000)
    num = -num if neg else num
    return num

def parse_html(urls_filename):

    outfile = file('out.json','w')    
    urls = file(urls_filename)

    for url in urls.readlines():
        if url.startswith('#'):
            year = int(url[1:])
            total_planned = 0
            total_used = 0
            print 'Year:',year
            continue
        
        if url.strip() == '':
            continue

        print 'URL:',url
        
        f = urllib2.urlopen(url)     

        last_code = None
        last_name = None
        top_budget = None
            
        for l in f.readlines():
            
            if year == None:
                m = year_re.findall(l)
                if len(m) > 0:
                    year = int(m[0])
                    print year
                continue
            
            if sep in l:
                top_budget = None
                    
            try:
                l=l.decode('iso8859-8')
                try:
                    used = l[33:56]
                    used = parse_number(used)
                except:
                    used = None
                try:
                    planned = l[57:80]
                    planned = parse_number(planned)
                except:
                    planned = None
                name = l[83:110]
                name = name.replace('*','').strip()
                assert( '==' not in name )
                assert( '--' not in name )
                assert( name != '' )
                name = name[-1:0:-1]+name[0]
                code = code_re.findall(l[120:])
            
                if len(code)>0:
                    code = ''.join(code)
                    if top_budget == None:
                        code = '00'+code
                        top_budget = code
                    else:
                        code = top_budget + code
                else:
                    code = None
                    
                if code != None and code.startswith('0000'):
                    if used != None:
                        used = -used
                    if planned != None:
                        planned = -planned
                                  
                if (planned != None or used != None) and name != None and code != None:
                    outfile.write(json.dumps({'code':code,'title':name,'gross_revised':planned,'gross_used':used,'year':year})+'\n')
                    if len(code) == 4 and code != '0000':
                        total_planned += planned
                        total_used += used
                    last_code = None
                    last_name = None
                elif (planned != None or used != None) and name == u'ברוטו' and last_code != None:
                    if len(last_code) == 4 and last_code != '0000':
                        total_planned += planned
                        total_used += used
                    outfile.write(json.dumps({'code':last_code,'title':last_name,'gross_revised':planned,'gross_used':used,'year':year})+'\n')
                elif planned == None and used == None and name != None and code != None:
                    last_code = code
                    last_name = name
                
            except Exception, e:
                #print e
                continue 
            
            if top_budget == None:
                continue

        outfile.write(json.dumps({'code':'00','title':'המדינה','gross_revised':total_planned,'gross_used':total_used,'year':year})+'\n')
        
        
parse_html('urls')