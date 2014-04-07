import sys
import os
import glob
import yaml
import logging

def collect_processors():
    current_path = "." # os.path.abspath(".")
    for dirpath, dirnames, filenames in os.walk(current_path):
        processors = [ f for f in filenames if f.endswith("yaml") ]
        for processor in processors:
            parsed = yaml.load(file(os.path.join(dirpath,processor)).read())['rules']
            for p in parsed:
                p['_basepath'] = dirpath
                p['_filename'] = processor
                #logging.info("PROCESSOR %r" % p)
                yield p

def is_relevant_processor(processor):
    basepath = processor['_basepath']
    input = processor['input']
    if type(input) == str:
        input = os.path.join(basepath,input)
        if '*' in input:
            input = glob.glob(input)
    elif type(input) == list:
        input = [ os.path.join(basepath,x) for x in input ]
    output = processor['output']
    if output.startswith("/"):
        src,dst = output.split('/')[1:3]
        output = [ x.replace(src,dst) for x in input ]
        tuples = zip(input,output)
        tuples = [ (i,o) for i,o in tuples if
                    os.path.exists(i) and
                    ((os.path.exists(o) and os.path.getmtime(i) > os.path.getmtime(o)) or
                    (not os.path.exists(o))) ]
        ret = len(tuples)>0
    else:
        list_input = input
        if type(input) != list:
            list_input = [ list_input ]
        ret = all([os.path.exists(i) for i in list_input])
        modified_times = [ os.path.getmtime(i) for i in list_input if os.path.exists(i) ]
        output = os.path.join(basepath,output)
        ret = ret and ((not os.path.exists(output)) or (len(modified_times)>0 and max(modified_times) > os.path.getmtime(output)))
        tuples = [ (input, output) ]
    #logging.info("PROCESSOR %sRELEVANT%r" % ("" if ret else "NOT ", p))
    processor['_tuples'] = tuples
    return ret

def run_processor(processor,apikey):
    for inputs,output in processor['_tuples']:
        processor_classname = processor['processor']
        processor_module = "processors."+processor_classname
        processor_class = __import__(processor_module, globals(), locals(), [processor_classname], -1).__dict__.get(processor_classname)
        processor_obj = processor_class()
        params = processor.get('params',{})
        if processor_classname == "upload":
            params['APIKEY'] = apikey
        logging.info("%s(%s) %s << %s" % (processor_classname,
                                         ", ".join("%s=%s" % i for i in params.iteritems()), output,
                                         " + ".join(inputs) if type(inputs)==list else inputs))
        try:
            processor_obj.process(inputs,output,**params)
        except Exception,e:
            logging.error("%s(%s) %s, deleting %s" % (processor_classname,
                                             ", ".join("%s=%s" % i for i in params.iteritems()), e, output))
            os.unlink(output)
            raise

def setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)

if __name__ == "__main__":
    APIKEY = None
    if len(sys.argv) > 1:
        APIKEY = sys.argv[1]
    setup_logging()
    processors = list( collect_processors() )
    while True:
        relevant = [ p for p in processors if is_relevant_processor(p) ]
        if len(relevant) == 0:
            break
        for p in relevant:
            run_processor(p,APIKEY)
