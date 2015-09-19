#encoding: utf8
import json
import sys
from collections import OrderedDict

def getSizeOf(obj):
    import cPickle
    return "%0.3fMB" % (len(cPickle.dumps(obj))/1024.0/1024)

class LimitedSizeDict(OrderedDict):
  def __init__(self, *args, **kwds):
    self.size_limit = kwds.pop("size_limit", None)
    OrderedDict.__init__(self, *args, **kwds)
    self._check_size_limit()

  def __setitem__(self, key, value):
    OrderedDict.__setitem__(self, key, value)
    self._check_size_limit()

  def _check_size_limit(self):
    if self.size_limit is not None:
      while len(self) > self.size_limit:
        self.popitem(last=False)

# Holds information regarding budget items
class BudgetItems(object):
    def __init__(self,in_fn,curatedInputs,errors):
        self.minYear = 10000
        self.maxYear = 0
        self.titleCodeYears = {}
        self.num_budgets = 0
        self.codes = {}
        self.titles = {}
        self.equivs = {}
        self.skipped = {}
        for line in file(in_fn):
            data = json.loads(line)
            self.num_budgets += 1

            year = data['year']
            title = data['title']
            code = data['code']
            equivs = data.get('equiv_code',[])
            test_value = sum(data.get(x,0)**2 for x in ['net_allocated','gross_allocated','net_revised','commitment_allocated','net_used'])
            active = data.get('active',True)
            if test_value == 0 or not active:
                print "SKIPPING non-active %d/%s" % (year,code)
                errors.skipped(year,code)
                self.skipped.setdefault(year, []).append(code)
                continue

            self.codes.setdefault(year, []).append(code)

            self.minYear = min(self.minYear,year)
            self.maxYear = max(self.maxYear,year)

            self.titleCodeYears.setdefault((title,code),[]).append(year)
            self.titles.setdefault(title,{}).setdefault(year,[]).append(code)

            equivs = [ e.split('/') for e in equivs ]
            for y,c in equivs:
                y = int(y)
                if y != year:
                    self.equivs.setdefault((y,c),{}).setdefault(year,[]).append(code)

        for curatedInput in curatedInputs:
            curated = json.load(file(curatedInput))
            for single in curated:
                src,dest = single
                srcYear,srcCode = src
                if len(srcCode)==10:
                    self.codes[srcYear].append(srcCode)

        print "Budgets processed #%d recs" % self.num_budgets
        print "Years %d..%d" % (self.minYear,self.maxYear)

    def allCodes(self,year):
        return sorted(self.codes[year],key=lambda x:-len(x))

    def skippedCodes(self,year):
        return self.skipped.get(year,[])

class EquivsBase(object):

    HEURISTIC = False

    def __init__(self,size_limit=None):
        self.equivs = LimitedSizeDict()

    def key(self,year,code):
        return "%d/%s" % (year,code)

    def _put(self,srcYear,srcCode,dstYear,dstCodes):
        eqs = self.equivs.setdefault(self.key(srcYear,srcCode),{})
        if eqs.has_key(dstYear) and eqs[dstYear] != dstCodes:
            print "DUP %s/%s <-- %s/%s (already has %s)" % (srcYear,srcCode,dstYear,dstCodes,eqs[dstYear])
        eqs[dstYear] = dstCodes

    def get(self,srcYear,srcCode):
        return self.equivs.get(self.key(srcYear,srcCode),{})

    def getMinYear(self,srcYear,srcCode,minYear):
        per_year = self.get(srcYear,srcCode)
        per_year = list(per_year.iteritems())
        per_year = filter(lambda x:x[0]>=minYear,per_year)
        if len(per_year) > 0:
            per_year.sort(key=lambda x:x[0]) # sort by year ascending
            first = per_year[0]
            if first[1] == '':
                return first[0],[]  # handle empty lists
            else:
                return first[0],first[1].split(";") # return first batch of codes
        else:
            return None,None

    def getEquivs(self,srcYear,srcCode,dstYear):
        return self.getMinYear(srcYear,srcCode,dstYear)

    def setEq(self,srcYear,srcCode,dstYear,dstCodes):
        dstCodes = ";".join(sorted(dstCodes))
        self._put(srcYear,srcCode,dstYear,dstCodes)
        #self._put(dstYear,dstCodes,srcYear,srcCode)

class YearlyEquivs(EquivsBase):
    def __init__(self,budgetItems,curatedInputs,errors):
        super(YearlyEquivs,self).__init__()
        for key,years in budgetItems.titleCodeYears.iteritems():
            title,code = key
            years = sorted(years)
            years = zip(years[1:],years[:-1])
            for srcYear,dstYear in years:
                self.setEq(srcYear,code,dstYear,[code])
        budgetItems.titleCodeYears = None
        for curatedInput in curatedInputs:
            curated = json.load(file(curatedInput))
            for single in curated:
                src,dest = single
                srcYear,srcCode = src
                dstYear = list(set(k[0] for k in dest))
                dstCodes = list(set(k[1] for k in dest))
                assert(len(dstYear)) == 1
                dstYear = dstYear[0]
                self.setEq(srcYear,srcCode,dstYear,dstCodes)
                errors.curated(srcYear, srcCode, dstYear, dstCodes)

class DescendantEquivs(EquivsBase):
    def __init__(self,bi):
        super(DescendantEquivs,self).__init__()
        for year in range(bi.minYear,bi.maxYear+1):
            kids = {}
            for code in bi.allCodes(year):
                if len(code)>4:
                    parent = code[:len(code)-2]
                    kids.setdefault(parent,[]).append(code)
            for parent,descendants in kids.iteritems():
                self.setEq(year,parent,year,descendants)

    def getEquivs(self,srcYear,srcCode,dstYear):
        return self.getMinYear(srcYear,srcCode,srcYear)

class SameNameCommonParentEquivs(EquivsBase):

    HEURISTIC = True

    def __init__(self,bi):
        super(SameNameCommonParentEquivs,self).__init__()
        for title, years in bi.titles.iteritems():
            options = []
            for year,codes in years.iteritems():
                # codes here are all the budget code in <year> which are named <title>
                for code in codes:
                    # make sure this title is unique among its siblings
                    parentlen = None
                    for i in range(2,len(code),2):
                        candidate = code[:i]
                        if len(filter(lambda x:x.startswith(candidate),codes))==1:
                            parentlen = len(candidate)
                            break
                    if parentlen is not None:
                        options.append((year,code,parentlen))
            for y1,c1,pl1 in options:
                for y2,c2,pl2 in options:
                    if y1<=y2 or c1==c2:
                        continue
                    # find the equivalents for (y1,p1) in y2
                    pl = max(pl1,pl2)
                    p1 = c1[:pl]
                    p2 = c2[:pl]
                    eqs = bi.equivs.get((y1,p1),{}).get(y2,[])
                    if len(eqs)==1:
                        eq = eqs[0]
                        if p2==eq:
                            # Yay, we got a match!
                            # print "OOO",y1,c1,pl1,p1,"->",y2,c2,pl2,p2,"/",eq
                            self.setEq(y1,c1,y2,[c2])

    def getEquivs(self,srcYear,srcCode,dstYear):
        return self.getMinYear(srcYear,srcCode,dstYear)

class MatcherResults(object):
    def __init__(self):
        self.cache = {}
        self.matches = {}

    def _add(self,srcYear,srcCode,dstYear,dstCode):
        dstKey = "%d/%s" % (dstYear,dstCode)
        srcKey = "%d/%s" % (srcYear,srcCode)
        self.cache.setdefault(dstKey,{'code':dstCode,'year':dstYear,'equiv_code':set([dstKey])})['equiv_code'].add(srcKey)

    def set(self,srcYear,srcCode,dstYear,codes):
        for code in codes:
            self._add(srcYear,srcCode,dstYear,code)
        if len(codes)==1:
            self._add(dstYear,codes[0],srcYear,srcCode)
        if srcYear == dstYear + 1:
            self.matches.setdefault(srcYear,[]).append(srcCode)

    def dump(self,out_fn):
        out = file(out_fn,"w")
        for row in self.cache.values():
            row['equiv_code'] = sorted(list(row['equiv_code']))
            out.write(json.dumps(row,sort_keys=True)+"\n")

    def stats(self):
        ret = {}
        for year,matches in self.matches.iteritems():
            ret[year] = {'matches':len(matches),'levels':{}}
            for i in range(2,10,2):
                ret[year]['levels'][str(i)] = {'matches':len(filter(lambda x:len(x)==i+2,matches))}
        return ret

    def getForYear(self,year):
        return self.matches[year]

class ErrorCollector(object):
    def __init__(self):
        self.errors = {}

    def missing(self,srcYear,tgtYear,code):
        if srcYear == tgtYear + 1:
            self.errors.setdefault(srcYear,{}).setdefault(code,{})['missing']=True

    def skipped(self,year,code):
        self.errors.setdefault(year,{}).setdefault(code,{})['skipped']=True

    def invalid(self,srcYear,srcCode,tgtYear,alt):
        if srcYear == tgtYear + 1:
            self.errors.setdefault(srcYear,{}).setdefault(srcCode,{})['invalid']=alt

    def curated(self,srcYear,srcCode,tgtYear,tgtCodes):
        if srcYear == tgtYear + 1:
            self.errors.setdefault(srcYear,{}).setdefault(srcCode,{})['curated']=tgtCodes

    def heuristic(self,srcYear,srcCode,tgtYear,codes):
        if srcYear == tgtYear + 1:
            self.errors.setdefault(srcYear,{}).setdefault(srcCode,{})['heuristic']=codes

    def getForYear(self,year):
        return self.errors.get(year)

    def stats(self):
        ret = {}
        for year,codes in self.errors.iteritems():
            ret[year] = {'missing':0,'invalid':0,'levels':{}}
            for i in range(2,10,2):
                ret[year]['levels'][str(i)] = {'missing':0,'invalid':0}
            for code,status in codes.iteritems():
                level = len(code)-2
                if level > 0:
                    level = str(level)
                    if status.get('missing',False):
                        ret[year]['missing'] += 1
                        ret[year]['levels'][level]['missing'] += 1
                    if len(status.get('invalid',[]))>0:
                        ret[year]['invalid'] += 1
                        ret[year]['levels'][level]['invalid'] += 1
        return ret

    def dump(self,out_fn,bi):
        out = file(out_fn,'w')
        for year in range(bi.minYear+1,bi.maxYear+1):
            for l in [bi.allCodes(year),bi.skippedCodes(year)]:
                for code in l:
                    error = self.errors[year].get(code,{})
                    error['pending'] = ""
                    rec = {'code':code,'year':year,'match_status':error}
                    out.write(json.dumps(rec,sort_keys=True)+"\n")

class MatchValidator(object):
    def __init__(self,errors):
        self.codes = {}
        self.errors = errors

    def clear(self):
        self.codes = {}

    def check(self,srcYear,srcCode,dstYear,codes):
        if srcYear == dstYear + 1:
            current = self.codes.setdefault(srcYear, {}).setdefault(len(srcCode),[])
            for code in codes:
                assert(len(code)>0)
                for c in current:
                    if c.startswith(code) or code.startswith(c):
                        print "INVALID: %s/%s --> %s/%s (already have %s)" % (srcYear,srcCode,dstYear,code,c)
                        self.errors.invalid(srcYear,srcCode,dstYear,[code,c])
                        return False
            current.extend(codes)
        return True

class Matcher(object):
    def __init__(self,results,algos,validator):
        self.results = results
        self.algos = algos
        self.validator = validator
        self.cache = EquivsBase(size_limit=50000)
        self.algos.insert(0,self.cache)

    def match(self,srcYear,srcCode,dstYear):
        equivs = [(srcYear,srcCode)]
        # print ">>>>>> ",srcYear,srcCode,"->",dstYear
        done = False
        heuristic = False
        while not done:
            # We stop when all years are dstYear or we can't proceed no more
            if any(x[1] == "MISS" for x in equivs):
                break
            years = list(set(eq[0] for eq in equivs))
            if len(years)==1 and years[0] == dstYear:
                # Great! we're done, save to cache
                codes = list(set(eq[1] for eq in equivs))
                if self.validator.check(srcYear,srcCode,dstYear,codes):
                    # print "MATCH :%d/%s: --> %s" % (srcYear,srcCode,",".join(":%d/%s:" % (dstYear,c) for c in codes))
                    self.cache.setEq(srcYear,srcCode,dstYear,codes)
                    self.results.set(srcYear,srcCode,dstYear,codes)
                    return equivs,heuristic
                else:
                    break
            new_equivs = []
            for year,code in equivs:
                success = False
                for algo in self.algos:
                    eqYear,eqCodes = algo.getEquivs(year,code,dstYear)
                    if eqYear is not None:
                        new_equivs.extend([(eqYear,eqCode) for eqCode in eqCodes])
                        # print year,code,"-"+algo.__class__.__name__+"->",eqYear,eqCodes
                        heuristic = heuristic or algo.HEURISTIC
                        success = True
                        break
                if success:
                    continue
                # miss
                # print "MISS :%d/%s: -/-> %d/????" % (srcYear,srcCode,dstYear)
                done = True
                break
            equivs = new_equivs
        self.cache.setEq(srcYear,srcCode,dstYear,["MISS"])
        return None,None

def main(budgets_input,curated_inputs,missing_output,equivs_output,stats_file):
    # Here we hold the errors during the process
    errors = ErrorCollector()
    # load all budget items
    bi = BudgetItems(budgets_input,curated_inputs,errors)
    # create equivalents between subsequent years
    yearEqs = YearlyEquivs(bi,curated_inputs,errors)
    # create equivalents between items and their descendants
    descEqs = DescendantEquivs(bi)
    # try to match similar names budget items with common parents
    sncpEqs = SameNameCommonParentEquivs(bi)

    minYear = bi.minYear
    maxYear = bi.maxYear

    # Here we hold the matches
    results = MatcherResults()
    # Here we check everything's valid
    validator = MatchValidator(errors)
    # And this does the actual matching
    matcher = Matcher(results,[yearEqs,descEqs,sncpEqs],validator)
    # We find matches for all budget years:
    for srcYear in range(minYear+1,maxYear+1):
        validator.clear()
        # in all previous years
        for tgtYear in range(srcYear-1,minYear-1,-1):
            # iterate on all budget codes, from specific to generic:
            print srcYear, tgtYear
            for srcCode in bi.allCodes(srcYear):
                equivs,heuristic = matcher.match(srcYear,srcCode,tgtYear)
                if equivs is None:
                    errors.missing(srcYear,tgtYear,srcCode)
                if heuristic:
                    errors.heuristic(srcYear,tgtYear,srcCode)

    # Report
    error_stats = errors.stats()
    match_stats = results.stats()
    stats = {}
    for year in range(minYear+1,maxYear+1):
        stat = error_stats.get(year,{})
        stat['matches'] = match_stats.get(year,{}).get('matches',0)
        for i in range(2,10,2):
            l = str(i)
            matches = match_stats.get(year,{}).get('levels',{}).get(l,{}).get('matches',0)
            stat.setdefault('levels',{}).setdefault(l,{})['matches'] = matches
        stats[year] = stat
    print json.dumps(stats,indent=2)
    stats = {'key':'match-stats','value':stats}
    file(stats_file,'w').write(json.dumps(stats))

    # dump output
    errors.dump(missing_output,bi)
    results.dump(equivs_output)

class item_connections(object):
    def process(self,input_file,output_file,errors_file=None,curated=[],match_stats=None):
        main(input_file,curated,errors_file,output_file,match_stats)

if __name__=="__main__":
    main("test/budgets.jsons",
         ["test/2013-2012-conversion.json","test/curated.json","test/curated2.json","test/curated5.json"],
         "test/missing.jsons","test/equivs.jsons","test/stats.json")
