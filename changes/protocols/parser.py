# -*- coding: utf-8 -*-
import os
import csv
import re
import glob
from pyth.plugins.rtf15.reader import Rtf15Reader
from pyth.plugins.plaintext.writer import PlaintextWriter

headerColumns = ['תאריך', 'ישיבה']

#REQUEST_RE = re.compile(u"(\u05e4\u05e0\u05d9\u05d9?(\u05d4|\u05d5\u05ea)\s+(\u05de\u05e1(\u05e4\u05e8|'|))?[-\s\dעד,]+)")
DIGITS_RE = u"\d[-\s\dועד/,]*\d"
REQUEST_RE = re.compile(u"(\u05e4x\u05e0\u05d9\u05d9?(\u05d4|\u05d5\u05ea)[^.]{1,10}"+DIGITS_RE+u")")
APPROVEDLINE_RE = re.compile(u'('+DIGITS_RE+u'[^%\u05dc\u05d0]*\u05d0\u05d5\u05e9\u05e8([\u05d4\u05d5/])?)')
DOUBLES_RE = re.compile(u'(\d+)\s*(-|עד)\s*(\d+)')
DOUBLES_RE2 = re.compile(u'(\d{2})/?(\d{3})')
DOUBLES_RE3 = re.compile(u'(\d{3})\((\d{2})\)')
SINGLES_RE = re.compile(u'(\d+)')
BAD_WORDS = [ u'של', u'בעמוד' ]

CSV_PATH = "../*.csv"
RTF_PATH = "*.rtf"

def parse():
    committeeIdsPerYear = {}
    for csvFileName in glob.glob(CSV_PATH):
        if not re.match('.+\d{4}\.csv$', csvFileName):
            continue

        year = csvFileName[-8:-4]
        if int(year) > 2010:
            continue

        committeeIdsPerYear[year] = set()
        
        with open(csvFileName) as csvFile:
            for row in csv.reader(csvFile):
                committeeId = row[8]
                if row[0].strip() == year:
                    if row[6] == '2' and committeeId != '0':
                        committeeIdsPerYear[year].add(committeeId)
                    committeeIdsPerYear[year].add("%03d-%02d" % (int(row[2]),int(row[1])))

    requestToMeetingMap = {}
    with open('./log.txt', 'w+') as outputFile:
        rtfFiles = glob.glob(RTF_PATH)
        rtfFiles.sort()
        for fileName in rtfFiles:
            if not fileName.endswith('.rtf'):
                continue

            year = fileName[:4]
            if year not in committeeIdsPerYear:
                continue
            if year not in requestToMeetingMap:
                requestToMeetingMap[year] = {}

            hadAnything = False
            with open(fileName) as rtfFile:
                parsedName = re.findall(u'\d+', fileName)
                date, meetingId = str('/'.join(parsedName[0:3][::-1])), parsedName[-1] if len(parsedName) > 3 else '00'
                try:
                    doc = Rtf15Reader.read(rtfFile)
                except Exception, e:
                    print "failed to parse %s: %s" % (fileName,e)
                    continue

                for line in PlaintextWriter.write(doc):
                    line = unicode(line, encoding='utf-8')

                    if u'אושר' in line and len(line)<95:
                        print fileName+":"+line
                    for _request in REQUEST_RE.findall(line) + APPROVEDLINE_RE.findall(line):
                        request = _request[0]
                        hadAnything = True
                        ids = set()
                        doubles2 = set(DOUBLES_RE2.findall(request))
                        for d in doubles2:
                            p1,p2 = d
                            combination_id = '%s-%s' % (p2,p1)
                            print "D2 "+combination_id
                            if combination_id in committeeIdsPerYear[year]:
                                ids.add(combination_id)
                        request = DOUBLES_RE2.subn('',request)[0]
                        doubles3 = set(DOUBLES_RE3.findall(request))
                        for d in doubles3:
                            p1,p2 = d
                            combination_id = '%s-%s' % (p1,p2)
                            print "D3 "+combination_id
                            if combination_id in committeeIdsPerYear[year]:
                                ids.add(combination_id)
                        request = DOUBLES_RE3.subn('',request)[0]
                        doubles = set(DOUBLES_RE.findall(request))
                        for d in doubles:
                            p1,sep,p2 = d
                            combination_id = '%s-%s' % (p1,p2)
                            if p1.startswith('0') and sep == '-':
                                ids.add(combination_id)
                            else:
                                if combination_id in committeeIdsPerYear[year]:
                                    ids.add(combination_id)
                                else:
                                    p1 = int(p1)
                                    p2 = int(p2)
                                    if abs(p2-p1) < 100:
                                        ids.update(map(str,range(min(p1,p2),max(p1,p2)+1)))
                        request = DOUBLES_RE.subn('',request)[0]
                        singles = SINGLES_RE.findall(request)
                        ids.update(singles)
                            
                        for word in BAD_WORDS:
                            if word in request:
                                ids = set()

                        res = list(ids & committeeIdsPerYear[year])

                        outputFile.write(fileName + ': ' + _request[0].strip().encode('utf-8')+"  " +repr(ids)+"->"+repr(res)+"\n")
                        outputFile.flush()
                                                      
                        for requestId in res:
                            requestToMeetingMap[year][requestId] = [date, meetingId]
            
            if not hadAnything:
                pass #os.rename(fileName,fileName+".empty")


    for csvFileName in glob.glob(CSV_PATH):
        if not re.match('.+\d{4}\.csv$', csvFileName):
            continue

        year = csvFileName[-8:-4]
        if not year in requestToMeetingMap:
            continue
                
        total = 0
        match = 0
        with open(csvFileName) as csvFile:
            with open(csvFileName[:-4] + '_out' + csvFileName[-4:], 'w+') as outputCsv:
                writer = csv.writer(outputCsv)
                reader = csv.reader(csvFile)
                writer.writerow(reader.next() + headerColumns)


                for row in csv.reader(csvFile):
                    if row[0].strip() == year:
                        committeeId1 = "%03d-%02d" % (int(row[2]),int(row[1]))
                        committeeId2 = None
                        relevant = False
                        if row[6] == '2' and row[8] != '0':
                            committeeId2 = row[8]

                        total += 1
                        if committeeId1 in requestToMeetingMap[year]:
                            match += 1
                            writer.writerow(row + requestToMeetingMap[year][committeeId1])
                        elif committeeId2 in requestToMeetingMap[year]:
                            match += 1
                            writer.writerow(row + requestToMeetingMap[year][committeeId2])
                        else:
                            writer.writerow(row + ['', ''])
                    else:
                        writer.writerow(row + ['', ''])

        print csvFileName, total, match

if __name__ == '__main__':
    parse()
