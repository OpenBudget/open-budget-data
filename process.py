import sys
import os
import glob
import yaml
import logging
import time
import subprocess

processor_order = [ 'download_shitty_csv',
                    'spreadsheet_to_jsons',
                    'download_pending_changes',
                    'scrape_supports',
                    'scrape_exemptions',
                    'new_budget_csv',
                    'rar_to_zip',
                    'combine_budget_jsons',
                    'prepare_budget_changes',
                    'csv_to_jsons',
                    'item_connections',
                    'aggregate_jsons_by_key',
                    'analyze_budgets',
                    'extract_txt_from_docs',
                    'extract_change_groups',
                    'concat',
                    'consolidate_change_dates',
                    'fix_changeline_budget_titles',
                    'fix_support_budget_titles',
                    'make_search_prefixes',
                    'process_entities',
                    'dump_to_db',
                    'upload',
		            'rss',
                    'extract_for_partition_layout',
                    'prepare_compare_record']
processor_order = dict( (e,i) for i,e in enumerate(processor_order) )

def collect_processors(start_here):
    current_path = start_here
    for dirpath, dirnames, filenames in os.walk(current_path):
        processors = [ f for f in filenames if f.endswith("yaml") ]
        for processor in processors:
            processor_fname = os.path.join(dirpath,processor)
            parsed = yaml.load(file(processor_fname).read())['rules']
            for p in parsed:
                p['_basepath'] = dirpath
                p['_filename'] = processor
                files = [os.path.join(dirpath,processor), os.path.join('processors',p['processor'])+'.py']
                p['_modtime'] = max(os.path.getmtime(x) for x in files)
                #logging.info("PROCESSOR %r" % p)
                yield p

def is_relevant_processor(processor):
    basepath = processor['_basepath']
    modtime = processor['_modtime']

    input = processor.get('input')
    if type(input) == str:
        input = os.path.join(basepath,input)
        if '*' in input:
            input = glob.glob(input)
    elif type(input) == list:
        input = [ os.path.join(basepath,x) for x in input ]
    elif input is None:
        input = []
    output = processor['output']
    delay = processor.get('delay',0)
    if output.startswith("/"):
        src,dst = output.split('/')[1:3]
        output = [ x.replace(src,dst) for x in input ]
        tuples = zip(input,output)
        tuples = [ (i,o) for i,o in tuples if
                    os.path.exists(i) and
                    ((os.path.exists(o) and max(modtime,os.path.getmtime(i)) > (delay+os.path.getmtime(o))) or
                    (not os.path.exists(o))) ]
        ret = len(tuples)>0
    else:
        list_input = input
        if type(input) != list:
            list_input = [ list_input ]
        ret = all([os.path.exists(i) for i in list_input])
        if len(input) > 0:
            modified_times = [ os.path.getmtime(i) for i in list_input if os.path.exists(i) ]
            modified_times.append(modtime)
        else:
            modified_times = [ time.time() ]
        output = os.path.join(basepath,output)
        ret = ret and ((not os.path.exists(output)) or (len(modified_times)>0 and max(modified_times) >  (delay+os.path.getmtime(output))))
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
        use_proxy = processor.get('use_proxy',False)
        if use_proxy:
            logging.info('Setting up proxy...')
            local_address = '127.0.0.1:55555'
            proxy = subprocess.Popen(['ssh','adamk@budget.msh.gov.il','-p','27628','-ND',local_address])
            time.sleep(10)
            params['PROXY'] = local_address
        try:
            processor_obj.process(inputs,output,**params)
        except Exception,e:
            logging.error("%s(%s) %s, deleting %s" % (processor_classname,
                                             ", ".join("%s=%s" % i for i in params.iteritems()), e, output))
            if os.path.exists(output):
                os.unlink(output)
            raise
        finally:
            if use_proxy:
                logging.info('Tearing down proxy...')
                proxy.kill()
                proxy.wait()

def setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    out = file('process.log','w')
    ch = logging.StreamHandler(out)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)

if __name__ == "__main__":

    import singleton
    me = singleton.SingleInstance()

    APIKEY = None
    if len(sys.argv) > 1:
        APIKEY = sys.argv[1]
    start_here = '.'
    if len(sys.argv) > 2:
        start_here = sys.argv[2]
    has_logging = False
    priorities = list
    processors = list( collect_processors(start_here) )
    while True:
        relevant = [ p for p in processors if is_relevant_processor(p) ]
        relevant.sort( key=lambda p: processor_order[p['processor']] )
        if len(relevant) == 0:
            break
        else:
            if not has_logging:
                setup_logging()
                has_logging = True
        logging.debug("relevant processors: %r" % [ r['processor'] for r in relevant ])
        run_processor(relevant[0],APIKEY)
