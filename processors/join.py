#encoding: utf8
import json
import logging
import sys
import gzip
import sqlite3
import Levenshtein
import os
import time

CLEAN_WORDS = [ u'בע"מ',
                u'בעמ',
                u"בע'מ",
                u'(חל"צ)',
                u'בע"מ.',
                u'אינק.',
                u'לימיטד',
                u'בע"מ"',
                u'בע,מ',
                u'עב"מ',
                u'בע"ם',
                u'(ע"ר)',
                u"(ע''ר)",
              ]

clean_strings = {}

def clean_string(s, max_len):
    s=s[:max_len]
    if clean_strings.has_key(s):
        return clean_strings[s]
    ret = s
    if len(s) < max_len:
        for _word in CLEAN_WORDS:
            word = " " + _word
            if s.endswith(word):
                ret = s[:-len(word)]
                break
    else:
        for _word in CLEAN_WORDS:
            for sublen in range(1,len(_word)+1):
                word = " " + _word[:sublen]
                if s.endswith(word):
                    ret = s[:-len(word)]
                    break
    clean_strings[s] = ret
    return ret


# def common_prefix(s1,s2):
#     return Levenshtein.ratio(s1,s2)>0.8

# DICTIONARY = "/usr/share/dict/words";
# TARGET = sys.argv[1]
# MAX_COST = int(sys.argv[2])

# Keep some interesting statistics
NodeCount = 0
#WordCount = 0

# The Trie data structure keeps a set of words, organized with one node for
# each letter. Each node has a branch for each letter that may follow it in the
# set of words.
class TrieNode:
    def __init__(self):
        self.word = None
        self.children = {}

        global NodeCount
        NodeCount += 1

    def insert( self, word, value ):
        node = self
        for letter in word:
            if letter not in node.children:
                node.children[letter] = TrieNode()

            node = node.children[letter]

        node.word = word
        node.value = value

# # read dictionary file into a trie
# trie = TrieNode()
# for word in open(DICTIONARY, "rt").read().split():
#     WordCount += 1
#     trie.insert( word )
#
# print "Read %d words into %d nodes" % (WordCount, NodeCount)

# The search function returns a list of all words that are less than the given
# maximum distance from the target word
def search( trie, word, maxCost ):

    # build first row
    currentRow = range( len(word) + 1 )

    results = []

    # recursively search each branch of the trie
    for letter in trie.children:
        searchRecursive( trie.children[letter], letter, word, currentRow,
            results, maxCost )

    return results

# This recursive helper is used by the search function above. It assumes that
# the previousRow has been filled in already.
def searchRecursive( node, letter, word, previousRow, results, maxCost ):

    columns = len( word ) + 1
    currentRow = [ previousRow[0] + 1 ]

    # Build one row for the letter, with a column for each letter in the target
    # word, plus one for the empty string at column 0
    for column in xrange( 1, columns ):

        insertCost = currentRow[column - 1] + 1
        deleteCost = previousRow[column] + 1

        if word[column - 1] != letter:
            replaceCost = previousRow[ column - 1 ] + 1
        else:
            replaceCost = previousRow[ column - 1 ]

        currentRow.append( min( insertCost, deleteCost, replaceCost ) )

    # if the last entry in the row indicates the optimal cost is less than the
    # maximum cost, and there is a word in this trie node, then add it.
    if currentRow[-1] <= maxCost and node.word != None:
        results.append( (node.word, currentRow[-1], node.value ) )

    # if any entries in the row are less than the maximum cost, then
    # recursively search each branch of the trie
    if min( currentRow ) <= maxCost:
        for letter in node.children:
            searchRecursive( node.children[letter], letter, word, currentRow,
                results, maxCost )

# start = time.time()
# results = search( TARGET, MAX_COST )
# end = time.time()
#
# for result in results: print result
#
# print "Search took %g s" % (end - start)

class join(object):
    def process(self,input,output,dst_file=None,src_field=None,join_field=None,dst_field=None,dst_field_name=None,max_len=35,max_cost=3):

        def get_tries():
            global NodeCount
            input_conn = sqlite3.connect(input)
            input_cur = input_conn.cursor()
            count = input_cur.execute("""SELECT COUNT(*) from data""")
            count = count.next()[0]
            logging.debug("got %r records in input" % count)

            for skip in range(0,count,30000):
                in_values = input_cur.execute("""SELECT value from data WHERE dirty=1 LIMIT 30000 OFFSET %d""" % skip)
                NodeCount = 0
                trie = TrieNode()
                for _value in in_values:
                    value = json.loads(_value[0])
                    join_value = value.get(join_field)
                    dst_value = value.get(dst_field)
                    if join_value is None or dst_value is None:
                        continue
                    trie.insert( clean_string(join_value,max_len), dst_value )
                logging.debug("built trie, %d nodes" % NodeCount)
                yield trie

        def get_updates(conn):

            matches = {}
            match_num = 0
            globally_unmatachable = set()
            for cost in range(max_cost):
                trie_num = 0
                for trie in get_tries():
                    cc = conn.cursor()
                    key_values = cc.execute("""SELECT key,value from data""")
                    key_values = ( (k,json.loads(v)) for k,v in key_values )
                    num = 0
                    unmatchable = set()
                    for k,v in key_values:
                        num += 1
                        if num % 1000 == 0:
                            logging.debug('Trie #%d/%d: processed %d records, %d matches' % (cost, trie_num, num,match_num))
                        if v.get(dst_field_name) is not None:
                            #print v.get('recipient'), v.get(dst_field_name)
                            continue
                        to_match = clean_string(v[src_field],max_len)
                        if v.get('dst_field_name') is not None:
                            match_num += 1
                            continue

                        if to_match in globally_unmatachable:
                            continue
                        if to_match in unmatchable:
                            continue

                        match = matches.get(to_match)
                        join_value = None
                        results = None
                        if match is None:
                            if len(to_match) < 5:
                                continue

                            results = search(trie,to_match,cost)
                            if len(results) > 1:
                                logging.error("got more than one match! for %s: %r" % (to_match,results))
                                globally_unmatachable.add(to_match)
                            if len(results) == 1:
                                results = results[0]
                                match = results[2]
                                logging.debug("MATCH for %s: %s (cost %d)" % (to_match,match,results[1]))

                        if match is not None:
                            match_num += 1
                            v[dst_field_name] = match
                            yield (json.dumps(v,sort_keys=True),k)
                            matches[to_match] = match
                        else:
                            unmatchable.add(to_match)

                    logging.debug('Trie #%d/%d: TOTAL processed %d records, %d matches' % (cost, trie_num, num,match_num))
                    trie_num += 1

        conn = sqlite3.connect(dst_file)

        outfile = file(output,"w")

        c = conn.cursor()
        c.executemany("UPDATE data set value=?, dirty=1 where key=?", get_updates(conn))
        conn.commit()
        conn.close()

        time.sleep(10)
        file(output,"w").write("OK")


if __name__ == "__main__":
    input, output, dst_file, src_field, join_field, dst_field, dst_field_name = sys.argv[1:8]
    processor = join().process(input, output, dst_file, src_field, join_field, dst_field, dst_field_name)
