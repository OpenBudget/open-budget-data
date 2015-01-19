#!/usr/bin/python
#encoding: utf8

from exemption_record import exemption_record, numerate_date

def exemption_records_since_summary( since_date ):

    since_date = numerate_date(since_date)

    for curr_exemption_record in exemption_record.iter_records():

        if not curr_exemption_record.has_updated_since(since_date):
            continue
        
        yield {
            'exemption_record':curr_exemption_record,
            'entity_record':curr_exemption_record.get_entity()
        }





STYLE= """table#nice_table, table#nice_table th, table#nice_table td {
    border: 0px solid black;
    border-collapse: collapse;
    direction: rtl;
    font-size: medium;
    #margin-top: 20px;
    #margin-bottom: 20px;
}
table#nice_table th, table#nice_table td {
    padding: 5px;
    text-align: right;
}
table#nice_table td#marked {
    background-color: #5c5;
}
table#nice_table td#framecell {
    background-color: rgba(183, 211, 242, 0.32);
}
#table#nice_table tr:nth-child(even) {
#    background-color: #eee;
#}
#table#nice_table tr:nth-child(odd) {
#   background-color:#fff;
#}
#table#nice_table th{
#    background-color: gray;
#    color: white;
#}

table#basetable, table#basetable th, table#basetable td {
    padding-top: 20px
    padding-bottom: 20px
    border: 0px;
    direction: rtl
}


table#default_table, table#default_table th, table#default_table td {
    border: 0px;
    border-collapse: collapse;
    direction: rtl;
    font-size: medium;
    #margin-top: 20px;
    #margin-bottom: 20px;
}
table#default_table th, table#default_table td {
    padding: 3px;
    text-align: right;
}
table#default_table tr:nth-child(even) {
    background-color: transparent;
}
table#default_table tr:nth-child(odd) {
   background-color: transparent;
}
table#default_table th{
    background-color: transparent;
    color: black;
}




table#transparent_table {
    border: 0px;
    border-collapse: collapse;
    background-color: transparent;
}
"""

def table_data( r, tag, widths=None ):

    r = [unicode(x) if x is not None else '' for x in r]

    if widths is None:
        return ''.join(['<%s>%s</%s>' % (tag, r[i].encode('utf8'), tag) for i in xrange(len(r))])
    else:
        return ''.join(['<%s width=%s>%s</%s>' % (tag, widths[i], r[i].encode('utf8'), tag) for i in xrange(len(r))])

def supplier_str( curr_exemption_record ):
    ret = curr_exemption_record['supplier']
    
    if (curr_exemption_record['supplier_id'] is not None) and (curr_exemption_record['supplier_id'] != 0):
        ret += " (%d)" % (curr_exemption_record['supplier_id'])

    return ret

class nice_table:
    def __init__( self, headings, widths ):
        self.headings = headings
        self.widths = widths
        self.rows = []

    def add_row( self, row ):
        self.rows.append( row )
        return self

    def __str__( self ):
        s = sum(self.widths)
        widths = ['%d%%' % ((float(c)/s)*100) for c in self.widths]

        ret = ""
        ret += '<table id=nice_table>'
        ret += '<tr>' + table_data(self.headings, 'th',widths) + '</tr>'

        for row in self.rows:
            ret += '<tr>' + table_data(row, 'td', widths) + '</tr>'

        ret += '</table>'

        return ret

def change_history( curr_exemption_record ):
        # if len([h for h in curr_exemption_record['history'] if h['field'] == 'decision']) > 0:

        #     f.write( u"היסטוריית שינויים:<br>".encode('utf8') )

        #     t = nice_table( widths=[5, 20, 20],
        #                     headings=[u'תאריך', u'מ:', u'ל:'] )

        #     for h in summary_record['exemption_record']['history']:
        #         if h['field'] == 'creation':
        #             t.add_row ([
        #                 h['date'],
        #                 u'נוצרה הרשומה',
        #                 '-'
        #             ])
        #         elif h['field'] == 'decision':
        #             t.add_row ([
        #                 h['date'],
        #                 h['from'],
        #                 h['to']
        #             ])
        #     f.write( str(t) )
    
    #if len([h for h in curr_exemption_record['history'] if h['field'] == 'decision']) == 0:
    #    return None
        
    s = "<table id=default_table>"
    #s += table_data( ['', u'מ:', u'ל:'], 'th' )
    for h in curr_exemption_record['history']:
        if h['field'] == 'creation':
            s += tr(table_data( [h['date'], u'נוצרה הרשומה','',''], 'td' ))
        elif h['field'] == 'decision':
            s += tr(table_data( [h['date'], u'החלטה', u'מ ' + h['from'], u'ל ' + h['to']], 'td' ))
        elif h['field'] == 'volume':
            s += tr(table_data( [h['date'], u'היקף', u'מ ' + money_str(h['from']), u'ל ' + money_str(h['to'])], 'td' ))
        elif h['field'] == 'documents':
            s += tr(table_data( [h['date'], u'עודכנו מסמכים',''], 'td' ))
        elif h['field'] == 'description':
            s += tr(table_data( [h['date'], u'השתנה תיאור ההתקשרות', ''], 'td' ))
        elif h['field'] == 'start_date':
            s += tr(table_data( [h['date'], u'תאריך ההתחלה', u'מ ' + h['from'], u'ל ' + h['to']], 'td' ))
        elif h['field'] == 'end_date':
            s += tr(table_data( [h['date'], u'תאריך הסיום', u'מ ' + h['from'], u'ל ' + h['to']], 'td' ))
    s += "</table>"
    return s

def tag( s, tag, **args ):
    
    args = ' '.join( ['%s="%s"' % (k,v) for k,v in args.iteritems()] )

    if s is None:
        s = ''

    if type(s) is unicode:
        return '<%s %s>' % (tag, args) + s.encode('utf8') + '</%s>' % tag
    else:
        return '<%s %s>' % (tag, args) + s + '</%s>' % tag

def th( s, **args ):
    return tag(s, 'th', **args )

def td( s, **args ):
    return tag(s, 'td', **args )

def tr( s, **args ):
    return tag(s, 'tr', **args )

def table( s, **args ):
    return tag(s, 'table', **args )

def exemption_record_desc( summary_record ):
    rows = ""
    rows += tr( th(u'פרטי ההתקשרות', colspan='2') )
    rows += tr( th(u'מספר פרסום במנו"ף') + td('<a href='+summary_record['exemption_record']['url']+'>'+ str(summary_record['exemption_record']['publication_id']) +'</a>') )
    rows += tr( th(u'היקף') + td(money_str(summary_record['exemption_record']['volume'])) )
    rows += tr( th(u'תקנה / שלב') + td(summary_record['exemption_record']['regulation'] + ' / ' + summary_record['exemption_record']['decision']) )
    rows += tr( th(u'תקופת התקשרות') + td(summary_record['exemption_record']['start_date'] + ' - ' + summary_record['exemption_record']['end_date']) )
    if summary_record['exemption_record']['claim_date'] is not None:
        rows += tr( th(u'תאריך אחרון להגשת השגות') + td(summary_record['exemption_record']['claim_date']) )

    h = change_history( summary_record['exemption_record'] )
    if h is not None:
        rows += tr( th(u'היסטוריית שינויים', valign='top') + td(h) )
    
    docs_str = ''
    for doc in summary_record['exemption_record']['documents']:
        docs_str += '<a href=' + doc['link'].encode('utf8')+ '>'+ doc['description'].encode('utf8') +'</a><br>'
    rows += tr( th(u'מסמכים') + td(docs_str) )

    return table( id='nice_table', s=(rows) )

def money_str( n ):
    if (n == 0) or (n is None):
        return u'לא צויין'

    s = u''
    while n > 0:
        part = n % 1000
        n /= 1000
        if n > 0:
            s = unicode('%03d' % part) + s
            s = ',' + s
        else:
            s = unicode(part) + s
    return s + u' ש"ח'

def supplier_offices( summary_record, field_name ):
    ret = []
    for office_name in summary_record['entity_record'][field_name]:
        count = len(summary_record['entity_record'][field_name][office_name])

        accepted = len([r for r in summary_record['entity_record'][field_name][office_name] if r['decision'] != u'טרום החלטת ועדה'])

        if count == accepted:
            curr = (u'%s (%d) <font size=1>' % (office_name, count)).encode('utf8')
        elif accepted == 0:
            curr = (u'%s (%d טרם אושרו) <font size=1>' % (office_name, count)).encode('utf8')
        else:
            curr = (u'%s (%d, %d טרם אושרו) <font size=1>' % (office_name, count, count - accepted)).encode('utf8')


        for i, r in enumerate(sorted(summary_record['entity_record'][field_name][office_name], 
                                     key=lambda x:x['publication_id'] ) ):

            #lambda x:numerate_date(x['start_date'])
            curr += '<a href='+r['url'].encode('utf8')+'>'+ str(i+1) +'</a> '
        curr += '</font>'

        ret.append(curr)
    return '<br>'.join( ret )

def supplier_desc( summary_record ):
    volume_str = money_str(summary_record['entity_record']['exemption_volume'])
    if( summary_record['entity_record']['missing_volume_exemption_count'] > 0 ):
        volume_str += u' (לא כולל %d רשומות ללא סכום)' % (summary_record['entity_record']['missing_volume_exemption_count'])

    ret = table( id='nice_table', s=(
        tr( th(u'פרטי הספק', colspan='2') ) + 
        tr( th(u'ספק') + td(supplier_str(summary_record['exemption_record'])) ) + 
        tr( th(u'סה"כ בקשות / הודעות פטור עבור ספק') + td(str(summary_record['entity_record']['exemption_count'])) ) + 
        tr( th(u'סה"כ היקף עבור ספק') + td(volume_str) ) + 
        tr( th(u'משרדים', valign='top') + td( supplier_offices(summary_record, 'exemption_offices') ) ) +
        tr( th(u'משרדים החל מ 2014', valign='top') + td( supplier_offices(summary_record, 'exemption_offices_2014') ) )
    ) )
    return ret

def office_desc( summary_record ):
    ret = table( id='nice_table', s=(
        tr( th(u'משרד') + td(summary_record['exemption_record']['publisher']) ) + 
        tr( th(u'סה"כ פטורים') + td(u'**בקרוב**') ) + 
        tr( th(u'היקף') + td(u'**בקרוב**') ) + 
        tr( th(u'היקף בתחום') + td(u'**בקרוב**') )
    ) )

    return ret

def exemption_records_since_summary_html( filename, since_date ):
    
    f = open( filename, 'w' )
    f.write( "<html><head><style>" + STYLE + "</style></head><body>" )


    f.write( '<table id=basetable>' )
    for summary_record in exemption_records_since_summary( since_date ):


        f.write( 
            tr( td( colspan=3, align='right', bgcolor='grey',
                    s='')))

        f.write( 
            tr( td( colspan=3, align='right', 
                    s='<br><br>'+tag( tag='b', s=(summary_record['exemption_record']['publisher'].encode('utf8') + ':<br>' +
                                                  summary_record['exemption_record']['description'].encode('utf8').replace('\n', '<br>')) ))))

        f.write( 
            tr( valign='top', 
                s=(
                    td( exemption_record_desc(summary_record), width='20' ) +
                    td( '', bgcolor='grey', width='2' ) + 
                    td( supplier_desc(summary_record), width='60' )# +
                    #td( '', bgcolor='grey', width='2' )# + 
                    #td( office_desc(summary_record) )# + 
                    #td('', width='40%') 
               )
            )
        )
        
        

    f.write( '</table>' )
    f.write( "</body>" )


if __name__ == "__main__":
    exemption_records_since_summary_html( '1.html', '18/1/2015' )

