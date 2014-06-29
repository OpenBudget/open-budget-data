#encoding: utf8

import pystache
import json
import urllib2
import itertools
import pprint
import shelve
import math
import jinja2
import datetime
import sys
import logging
from numpy import array
from itertools import chain, combinations, groupby

cache = shelve.open('api.cache',writeback=True)

fields = ['net_expense_diff',
          'gross_expense_diff',
          'allocated_income_diff',
          'commitment_limit_diff',
          'personnel_max_diff']

expense_fields = ['net_expense_diff','gross_expense_diff','allocated_income_diff']

def get_field(c,field):
    ret = c.get(field,0)
    if ret is None:
        ret = 0
    return ret

def transfer_code(change):
    return (change['year'],change['leading_item'],change['req_code'])

def avg(l):
    l = list(l)
    return 1.0*sum(l)/len(l)

def get_groups(changes):
    groups = get_url('changegroup/pending')
    groups = [ (g['group_id'],[(g['year'],int(t.split('-')[0]),int(t.split('-')[1])) for t in g['transfer_ids']]) for g in groups ]
    return groups

def get_url(url):
    url = url.encode('utf8')
    if not cache.has_key(url):
        try:
            logging.debug( "getting url %s" % url )
            data = json.loads(urllib2.urlopen("http://the.open-budget.org.il/api/"+url+"?limit=5000").read())
        except:
            logging.error( "Failed to get data for %s" % url )
            raise
        cache[url] = data
        try:
            cache.sync()
        except:
            pass
    else:
        data = cache[url]
    return data

def common_prefix(items):
    prefix = None
    for item in items:
        if prefix is None:
            prefix = item
        else:
            for i in range(len(prefix),-1,-2):
                if item.startswith(prefix[:i]):
                    prefix = prefix[:i]
                    break
    return prefix

def process_title(title):
    if type(title) == unicode:
        return title.replace(u'המשרד ל','').replace(u'משרד ה','').replace(u'משרד ל','')
    elif type(title) == list:
        return ", ".join(map(process_title,title))
    else:
        logging.error( "bad title kind %r" % title )
        assert(False)

def format_value(value):
    if value < 0:
        sign = '-'
        value = -value
    else:
        sign = ''
    if value < 1000:
        unit = ''
    else:
        value = value / 1000.0
        if value < 1000:
            unit = u'אלף '
        else:
            value = value / 1000.0
            if value < 1000:
                unit = u'מיליון '
            else:
                value = value / 1000.0
                unit = u'מיליארד '
    num = u"%f" % value
    num = num[:4]
    if num[3] == ".":
        num = num[:-1]
    if num.endswith(".0"):
        num = num[:-2]
    return u"%s%s %s\u20aa" % (sign,num,unit)

def format_title(template,value,titles):
    value = format_value(value*1000)
    titles = map(process_title,titles)
    if template == 'enlargement-allocation':
        return u"תוספת של %s ל%s" % (value,titles[0])
    if template == 'cutbacks-allocation':
        return u"קיצוץ בסך %s ב%s" % (value,titles[0])
    if template == 'commitment-allocation':
        return u"%s כהרשאה להתחייב לטובת %s" % (value,titles[0])
    if template == 'internal-change':
        return u"שינוי פנימי של %s בתקציב %s" % (value,titles[0])
    if template == 'transfer':
        return u"העברת %s מ%s ל%s" % (value,titles[0],titles[1])

    return u"%s %s %s" % (template,title,value)

def append_age(title,age):
    if age < 7:
        title += u" חדש!"
    elif age < 14:
        title += u" (מהשבוע שעבר)"
    else:
        title += u" (מלפני %d שבועות)" % (age / 7)
    return title

def enhance_item(item):
    item['value'] = sum(item.get(x,0) for x in ['net_expense_diff','gross_expense_diff','allocated_income_diff','commitment_limit_diff'])
    return item

def join_explanations(explanations):
    splits = [ex.split('\n') for ex in explanations]
    min_length = min(len(sp) for sp in splits)
    for i in range(1,min_length):
        ss = set("\n".join(sp[-i:]) for sp in splits)
        if len(ss)>1:
            break
    i = i-1
    return "\n".join("\n".join(sp[:-i]) for sp in splits)+"\n\n"+"\n\n".join(splits[0][-i:])

def prepare_rss(output_filename):
    pending_changes = get_url("changes/pending/all")
    groups = get_groups(pending_changes[:])
    pending_by = {}
    for ch in pending_changes:
        key = json.dumps(transfer_code(ch))
        pending_by.setdefault(key,[]).append(ch)
    logging.debug( "pending_by keys %r" % pending_by.keys() )
    pending_by = pending_by.iteritems()
    transfer_dict = {}
    for key,v in pending_by:
        k = json.loads(key)
        expl = get_url("change_expl/%02d-%03d/%d" % (k[1],k[2],k[0]))
        transfer_dict[key] = { 'explanation': expl,
                             'year': k[0], 'req_code': k[2], 'leading_item': k[1],
                             'items': [enhance_item(i) for i in v] }
    final_transfers = []
    for group_id, group in groups:
        transfers = []
        for k in group:
            key = json.dumps(k)
            tr = transfer_dict[key]
            main_codes = set(item['budget_code'][:4] for item in tr['items'])
            main_codes.discard('0047')
            if len(main_codes)<1:
                logging.warning( "deleting %s %r" % (key,tr['items']) )
                del transfer_dict[key]
                continue
            main_codes = list(main_codes)
            tr['main_code'] = main_codes[0]
            tr['key'] = key
            assert(len(main_codes)==1)
            transfers.append(tr)
        if len(transfers) == 0:
            continue
        #print "TT",group,len(transfers)
        group_transfers = { 'transfers': transfers,
                            'group_id': group_id,
                            'group': list(group),
                            'items': list(chain.from_iterable(tr['items'] for tr in transfers)) }
        group_transfers['date'] = group_transfers['items'][0]['date']
        tr_date = datetime.datetime.strptime(group_transfers['date'],"%d/%m/%Y")
        group_transfers['age'] = (datetime.datetime.now() - tr_date).days
        for tr in transfers:
            main_code = tr['main_code']
            tr['explanation'] = tr['explanation']['explanation']
            tr['main_budget_item'] = get_url('budget/%s/%d' % (main_code,tr['year']))
            tr['filt_items'] = filter(lambda x: x['budget_code'].startswith(main_code),tr['items'])
            tr['net_expense_diff'] = sum(map(lambda x:x['net_expense_diff'],tr['filt_items']))
            tr['gross_expense_diff'] = sum(map(lambda x:x['gross_expense_diff'],tr['filt_items']))
            tr['allocated_income_diff'] = sum(map(lambda x:x['allocated_income_diff'],tr['filt_items']))
            tr['expenses'] = tr['net_expense_diff']+tr['gross_expense_diff']+tr['allocated_income_diff']
            #print "LL", group, tr['key'], len(tr['filt_items']),tr['expenses']
            tr['personnel_max_diff'] = sum(map(lambda x:x['personnel_max_diff'],tr['filt_items']))
            tr['commitment_limit_diff'] = sum(map(lambda x:x['commitment_limit_diff'],tr['filt_items']))
            budget_codes = [x['budget_code'] for x in tr['filt_items']]
            closest_parent = common_prefix(budget_codes)
            #tr['common_parent_budget_item'] = get_url('budget/%s/%d' % (closest_parent,tr['year']))
            #tr['breadcrumbs'] = [get_url('budget/%s/%d' % (closest_parent[:x],tr['year']))['title'] for x in range(4,len(closest_parent)+1,2)]
            budget_item_history = get_url('budget/%s' % (closest_parent,))
            history_filt = [x for x in budget_item_history if x['net_allocated'] > 0 and x['net_revised'] > 0]
            performance_history = 1
            if len(history_filt)>0:
                performance_history = sum(1.0*x['net_revised']/x['net_allocated'] for x in history_filt)
                tr['performance_history'] = performance_history / len(history_filt)
                if performance_history < 1.0:
                    if performance_history != 0:
                        performance_history = 1.0/performance_history
                    else:
                        performance_history = 100
            tr['performance_score'] = performance_history
            changes = [ (code,get_url("changes/%s/%d" % (code,tr['year']))) for code in budget_codes ]
            tr['changes_score'] = max(len(x[1]) for x in changes)
            tr['filt_items'].sort(key=lambda x:x['budget_code'])
            grp_items = groupby(tr['filt_items'],lambda x:x['budget_code'][:6])
            grp_items = [ (k,list(v)) for k,v in grp_items ]
            grp_items.sort(key=lambda x:x[0])
            grp_items = [ ("%(code)s: %(title)s" % get_url('budget/%s/%s' % (k,tr['year'])), list(v)) for k,v in grp_items]
            grp_items = [ {'group':k,'changes':v,'value':sum(x['value'] for x in v)} for k,v in grp_items]
            for gi in grp_items:
                gi['value_str'] = format_value(1000*gi['value'])
            tr['plus_items'] = filter(lambda x:x['value']>0,grp_items)
            tr['minus_items'] = filter(lambda x:x['value']<0,grp_items)
            #print 'PPP', tr['plus_items']
            #print 'MMM', tr['minus_items']
            #print '---'

        group_transfers['plus_items'] = list(chain.from_iterable(x['plus_items'] for x in transfers))
        group_transfers['plus_items'].sort(key=lambda x:x['value'],reverse=True)
        group_transfers['minus_items'] = list(chain.from_iterable(x['minus_items'] for x in transfers))
        group_transfers['minus_items'].sort(key=lambda x:x['value'])
        group_transfers['filt_items'] = list(chain.from_iterable(x['filt_items'] for x in transfers))
        budget_codes = set(x['budget_code'] for x in group_transfers['filt_items'])
        group_transfers['filt_items'] = [{'budget_code':x['budget_code'],'budget_title':x['budget_title']} for x in group_transfers['filt_items']]
        supports = chain.from_iterable(get_url('supports/%s' % budget_code) for budget_code in budget_codes)
        recipients = {}
        for sup in supports:
            recipient = sup['recipient']
            recipients.setdefault(recipient,0)
            recipients[recipient] += sup['amount_supported']
        recipients = list(recipients.iteritems())
        recipients.sort(key = lambda x:-x[1])
        group_transfers['supports'] = [(x[0],format_value(x[1])) for x in recipients[:5]]

        template = None
        value = None
        req_title = None
        explanation = None
        if len(group) == 1:
            tr = transfers[0]
            if tr['expenses'] > 0:
                template = 'enlargement-allocation'
                value = tr['expenses']
            elif tr['expenses'] < 0:
                template = 'cutbacks-allocation'
                value = - (tr['expenses'])
            elif tr['commitment_limit_diff'] > 0:
                template = 'commitment-allocation'
                value = tr['commitment_limit_diff']
            elif tr['expenses'] == 0 and max(chain.from_iterable((x[f] for x in tr['items']) for f in expense_fields)) > 0:
                template = 'internal-change'
                value = max(sum(x[f] for x in tr['items'] if x[f]>0) for f in expense_fields)
            else:
                logging.error("No template found for %s" % tr['key'])
            group_transfers['template'] = template
            group_transfers['value'] = value
            group_transfers['titles'] = [tr['main_budget_item']['title']]
            req_title = tr['items'][0]['req_title']
            explanation = tr['explanation'].replace("\n","<br/>")
        else:
            filt = lambda x:x['expenses']
            minus_transfers = filter(lambda x:filt(x)<0,transfers)
            plus_transfers = filter(lambda x:filt(x)>0,transfers)
            value = sum(map(filt,plus_transfers))
            #print [t['key'] for t in minus_transfers], [t['key'] for t in plus_transfers], group, sum(map(filt,minus_transfers)), value
            assert(sum(map(filt,minus_transfers))+value==0)
            template = 'transfer'
            group_transfers['template'] = 'transfer'
            group_transfers['value'] = value
            title = lambda x:x['main_budget_item']['title']
            group_transfers['titles'] = [map(title,minus_transfers),map(title,plus_transfers)]
            req_title = " / ".join(set(tr['items'][0]['req_title'] for tr in transfers))
            explanation = join_explanations([tr['explanation'] for tr in transfers]).replace("\n","<br/>")

        score = None
        if template is not None:
            score = value * avg(tr['performance_score'] for tr in transfers) * avg(tr['changes_score'] for tr in transfers)
            score = score / (group_transfers['age'] + 14)
            group_transfers['score'] = score
            group_transfers['req_title'] = req_title
            group_transfers['explanation'] = explanation
            group_transfers['title'] = format_title(group_transfers['template'],group_transfers['value'],group_transfers['titles'])
            group_transfers['title'] = append_age( group_transfers['title'], group_transfers['age'] )
            final_transfers.append(group_transfers)
        else:
            logging.error( "no template for group %s %s %s" % (group,template,score) )
    final_transfers.sort(key=lambda x:-x['score'])
    for tr in final_transfers:
        logging.info("SCORE %s %s %s %r %r" % (tr['score'],
                                               tr['group'],
                                               "value:%s" % tr['value'],
                                               [x['performance_score'] for x in tr['transfers']],
                                               [x['changes_score'] for x in tr['transfers']]))

    output = file(output_filename,"w")
    now = datetime.datetime.now()
    delta = datetime.timedelta(days=7-now.weekday())
    start = (now+delta).date()
    end = (start+datetime.timedelta(days=2))
    if start.month == end.month:
        feed_title = "%d / %d-%d" % (start.month,start.day,end.day)
    else:
        feed_title = "%d/%d - %d/%d" % (start.day,start.month,end.day,end.month)

    to_write = {'rss_title':feed_title,
                'rss_items':[x['group_id'] for x in final_transfers]}
    for i,e in enumerate(final_transfers):
        to_write['rss_items[%s]' % e['group_id']] = e
    for k,v in to_write.iteritems():
        output.write(json.dumps({'key':k,'value':v})+'\n')

    # rendered = []
    # item_template = file('email_item_template.jinja.html').read().decode('utf8')
    # item_template = jinja2.Template(item_template)
    # for tr in final_transfers:
    #     #print tr['template'], tr['main_budget_item']['code'], tr['main_budget_item']['title'], tr['value'], "/".join(tr['breadcrumbs']), tr["score"]
    #
    #     rendered.append( {'title': "%(title)s (%(date)s)" % tr,
    #                       'description': item_template.render(tr),
    #                       'score': tr['score'],
    #                       'index': len(rendered)+1 } )
    #     #pprint.pprint(tr)
    # email_data = { 'feed': { 'title': feed_title }, 'entries': rendered }
    # email_template = file('email_template.mustache.html').read().decode('utf8')
    # out = pystache.render(email_template, email_data)
    # file('email.html','w').write(out.encode('utf8'))

    try:
        cache.close()
    except:
        pass

class rss(object):
    def process(self,input,output):
        prepare_rss(output)

if __name__ == "__main__":
    input = sys.argv[1]
    output = sys.argv[2]
    processor = rss().process(input,output)
