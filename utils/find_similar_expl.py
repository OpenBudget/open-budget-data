#encoding: utf8

import json
import csv

def fuzzy_substring(needle, haystack):
    """Calculates the fuzzy match of needle in haystack,
    using a modified version of the Levenshtein distance
    algorithm.
    The function is modified from the levenshtein function
    in the bktree module by Adam Hupp"""
    m, n = len(needle), len(haystack)

    # base cases
    if m == 1:
        return not needle in haystack
    if not n:
        return m

    row1 = [0] * (n+1)
    for i in range(0,m):
        row2 = [i+1]
        for j in range(0,n):
            cost = ( needle[i] != haystack[j] )

            row2.append( min(row1[j+1]+1, # deletion
                               row2[j]+1, #insertion
                               row1[j]+cost) #substitution
                           )
        row1 = row2
    return 1.0 - (1.0*min(row1)) / len(needle)
NEEDLES = [
u"שיקום תשתיות במגזר הכפרי",
u"תשתיות בהתיישבות",
u"גרעיני התיישבות",
u"כפרי סטודנטים",
u"מפוני גוש קטיף",
]

if __name__ == "__main__":
    found = {}

    a=u"""" שר האוצר מבקש את אישורה של ועדת הכספים של הכנסת להעברת סכום של 242,672 אלפי שקלים חדשים מסעיף 47 - רזרבה כללית לסעיף 04 - משרד ראש הממשלה, בהתאם לסעיף 12 (א) לחוק יסודות התקציב, התשמ"ה - 1985, כמפורט בתדפיס המצורף בזה. דברי הסבר: פנייה זו נועדה לתקצוב המטרות הבאות: 1. סך של 218,890 אלפי ש"ח בהוצאה בגין הרשאות עבר שעיקרם שיקום תשתיות במגזר הכפרי. 2. תקצוב תשתיות התיישבויות בהתאם לפירוט הבא: 12,000 אלפי ש"ח במחוז הצפון, 24,828 אלפי ש"ח במחוז מרכז, 8,304 אלפי ש"ח בהר חברון ו- 2,600 אלפי ש"ח במחוז הדרום. 3. סך של 2,500 אלפי ש"ח עבור קליטת עלייה בהתיישבות, 1,250 אלפי ש"ח למפוני גוש קטיף ו-11,000 אלפי ש"ח לגרעיני התיישבות, בהתאם לסיכום בין המשרדים. 4. סך של 3,000 אלפי ש"ח עבור כפרי סטודנטים בהתאם להחלטת ממשלה. בבקשה זו אין השפעה על כח אדם. """
    for needle in NEEDLES:
        print needle, fuzzy_substring(needle, a)

    for line in file("change_explanation/explanations.jsons"):
        data = json.loads(line)
        expl = data['explanation']
        if expl is None: continue
        for needle in NEEDLES:
            ret= fuzzy_substring(needle, expl)
            if ret > 0.85:
                found[(data['year'],data['leading_item'],data['req_code'])] = { 'explanation': expl, 'needle': needle }

    w = csv.writer(file('stav.csv','w'))

    for line in file("changes/changegroups.jsons"):
        data = json.loads(line)
        keys = set( key for key in found.keys() if key[0] == data['year'] )
        for tr in data['transfer_ids']:
            key = (data['year'],int(tr.split('-')[0]),int(tr.split('-')[1]))
            if key in keys:
                row = [ data['year'],tr,found[key]['needle'].encode('utf8'),found[key]['explanation'].encode('utf8'),"http://the.open-budget.org.il/stg/#transfer/%(group_id)s/%(year)s" % data ]
                w.writerow(row)
                break
