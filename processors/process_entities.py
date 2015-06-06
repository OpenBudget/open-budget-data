###encoding: utf8
import json
import bisect
import logging

class process_entities(object):

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
                    u'בע"מ (חל"צ)',
                    u'(ער)',
                    u'{ער}',
                    u'}ער{',
                    u'(חלצ)',
                  ]
    CLEAN_TITLES = [ u'עירית',
                    u'מ.א.',
                    u"מ.מ.",
                    u'מ.א',
                    u"מ.מ",
                  ]
    def __init__(self):
        self.CLEAN_PREFIXES = set()
        for w in self.CLEAN_WORDS:
            for i in range(1,len(w)+1):
                self.CLEAN_PREFIXES.add(" "+w[:i])

    def clean(self,word):
        done = False
        while not done:
            done = True
            for p in self.CLEAN_PREFIXES:
                if word.endswith(p):
                    word = word[:-len(p)]
                    done = False
                    break
        word = word.replace('"','').replace("'",'')
        for w in self.CLEAN_TITLES:
            if word.startswith(w+" "):
                word = word[len(w)+1:]

        return word

    # Do cross matching of entitiy names and entity ids
    def process(self,inputs,outputs,
                name_key=None,
                processed_file=None,
                non_processed_file=None,
                id_keys=None,
                id_key=None ):

        entities_file, match_file = inputs
        used_entities_file = outputs

        entities = []
        for line in file(entities_file):
            entities.append(json.loads(line))

        # In case the input file contains an id, use it
        entity_by_id = {}
        if id_key is not None:
            entity_by_id = dict((e[id_key],e) for e in entities if id_key in e.keys())

        # Sort entities by clean name
        entities.sort(key=lambda x:self.clean(x['name']))

        # Get all clean names
        entity_names = [self.clean(x['name']) for x in entities]

        # Output file for entities we matched (to be merged with the target model)
        processed_file = file(processed_file,'w')

        # Output file for entitites we didn't match
        non_processed_file = file(non_processed_file,'w')

        # Output file for entitites we used (to used for the Entity model)
        used_entities_file = file(used_entities_file,'w')


        matches = 0
        for line in file(match_file):
            line = json.loads(line)
            found = None

            # If we have an id key, let's use it
            if id_key is not None:
                match_value = line.get(id_key)
                # We canonize so that all entities with the same id have the same name
                found = entity_by_id.get(match_value)

            # Try to find the match value in the list of entity names
            match_value = self.clean(line.get(name_key))
            if found is None and match_value is not None:
                # We use bisect so we find prefixes of the name as well
                i = bisect.bisect_left(entity_names, match_value)
                if i != len(entity_names):
                    clean_found = self.clean(found['name'])
                    # Make sure that what we found is what we're looking for
                    if clean_found==match_value or (len(match_value) > 30 and clean_found.startswith(match_value)):
                        found = entities[i]

            # If we found something
            if found is not None:
                matches += 1 # print "||%s|||%s" % (match_value, clean_found)
                rec = {}
                for _key in id_keys:
                    rec[_key] = line[_key]
                if found.get('kind') is None:
                    logging.warn('Failed to get kind for entity with id %s' % found.get(id))
                    continue
                rec['entity_kind'] = found['kind']
                rec['entity_id'] = found['id']
                used_entities_file.write(json.dumps(found,sort_keys=True)+"\n")
                processed_file.write(json.dumps(rec,sort_keys=True)+"\n")
                continue
            non_processed_file.write(match_value.encode('utf8')+"\n")
        logging.debug("matched %d entities" % matches)
