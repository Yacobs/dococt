import sys
import getopt
from string import whitespace
import pprint
import logging
import codecs
import unicodedata
import json
import re

import pymongo
from pymongo import MongoClient

def main(argv):
    try:
        opts, args = getopt.getopt(argv, 'i:o:s:hdl:m:', ['inputfile=', 'outputfile=', 'schema=', 'help', 'debug', 'logfile=', 'mongo='])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
        
    inputFile = ''
    outputFile = ''
    schemaFile = ''
    logFile = 'event.log'
    debug = False
    mongoURI = ''
        
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(2)
        elif opt in ('-i', '--inputfile'):
            inputFile = arg
        elif opt in ('-o', '--outputfile'):
            outputFile = arg
        elif opt in ('-s', '--schema'):
            schemaFile = arg
        elif opt in ('-d', '--debug'):
            debug = True
        elif opt in ('-l', '--logfile'):
            logFile = arg
        elif opt in ('-m', '--mongo'):
            mongoURI = arg
        else:
            usage()
            sys.exit(2)
    
    if inputFile == "" or outputFile == "":
        usage()
        sys.exit(2)
    
    # get just the name, no extension
    namePieces = inputFile.split('/')
    namePieces2 = namePieces[-1].split('.')
    documentName = namePieces2[0]
    
    # open the log file
    if debug:
        logging.basicConfig(filename=logFile, format='%(levelname)s -- %(asctime)s -- %(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(filename=logFile, format='%(levelname)s -- %(asctime)s -- %(message)s', level=logging.WARNING)
        
    if schemaFile == "":
        schemaFile = inputFile.split('.')[0] + '.json'

    # read in the schema
    try:
        schemaFin = codecs.open(schemaFile, 'r', encoding='utf-8')
    except:
        logging.error("Error opening file: {}".format(schemaFile))
        sys.exit(1)
    schema = json.load(schemaFin, strict=False)
    schemaFin.close()

    # process the input file
    lines = []
    with codecs.open(inputFile, 'r', encoding='utf-8') as fin:
        lines = fin.readlines()
    
    # figure out the schema
    # detect page breaks and then build the footer/header schema
    schemize_footer_header(schema, lines)
    logging.debug("New schema:")
    logging.debug(pprint.pformat(schema))
    
    outputLines = initial_cleanup(schema, lines)
    
    outputParagraphed = reconnect_paragraphs(schema, outputLines)
    
    # time to convert the set of lines into an object -- eventually to become a JSON representation
    document = break_down(schema, outputParagraphed, documentName)
    with codecs.open('DICTIONARY.json', 'w', encoding='utf-8') as fout:
        json.dump(document, fout)
        
    if mongoURI != '':
        client = MongoClient(mongoURI)
        db = client.dococt
        indentures = db.indentures
        post_id = indentures.insert(document)
        logging.debug("Inserted document into the database.")
    
    # outputSentenced = reconnect_sentences(schema, outputParagraphed)

    # write to the output file
    with codecs.open(outputFile, 'w', encoding='utf-8') as fout:
        for line in outputParagraphed:
            fout.write(line)
    
    print "\nPage Remover Done!"
    sys.exit(0)
    
def break_down(schema, lines, documentName):
    """
        Given a schema and lines, break it down into pieces
        Returns a dictionary object, instead of a set of lines
    """
    
    document = {}
    document['name'] = documentName
    document['type'] = 'document'
    
    document['data'] = find_articles(schema, lines, 0, len(lines)-1)

    return document
    
def find_articles(schema, lines, start, end):

    data = []
    
    # find first article
    articleStart = next_match(schema["general"]["article_header"], lines, start, end)

    if articleStart > start:
        textBlock = {}
        textBlock['name'] = ''
        textBlock['type'] = 'text'
        textBlock['data'] = lines[start:articleStart]
        
        data.append(textBlock)
    
    # loop through and add all the other articles
    while articleStart < end:
    
        nextArticle = next_match(schema["general"]["article_header"], lines, articleStart+1, end)
        
        if articleStart+1 < nextArticle:
            article = {}
            article['name'] = lines[articleStart]
            article['type'] = 'article'
            article['data'] = find_sections(schema, lines, articleStart+1, nextArticle-1) #lines[articleStart+1:nextArticle]
            
            data.append(article)

        articleStart = nextArticle

    return data
        
def find_sections(schema, lines, start, end):

    data = []
    
    # find first section
    sectionStart = next_match(schema["general"]["section_header"], lines, start, end)
    
    if sectionStart > start:
        textBlock = {}
        textBlock['name'] = ''
        textBlock['type'] = 'text'
        textBlock['data'] = lines[start:sectionStart]
        
        data.append(textBlock)
        
    # loop through and add all the other articles
    while sectionStart < end:
    
        nextSection = next_match(schema["general"]["section_header"], lines, sectionStart+1, end)
        
        if sectionStart+1 < nextSection:
            article = {}
            article['name'] = lines[sectionStart]
            article['type'] = 'section'
            article['data'] = lines[sectionStart+1:nextSection] # find_sections(schema, lines, sectionStart+1, nextSection-1)
            
            data.append(article)

        sectionStart = nextSection

    return data
    
    
def next_match(regex, lines, start, end):
    nextMatch = end + 1
    for i in xrange(start, end):
        if re.search(regex, lines[i], re.UNICODE) is not None:
            nextMatch = i
            break
    
    return nextMatch
       
def reconnect_paragraphs(schema, lines):
    """
        Given a schema and a set of lines, reconnect paragraphs that have line breaks in the middle
    """
    outputLinesParagraphed = []
    skipLines = 0
    for i in xrange(0, len(lines)-1):
        
        if skipLines > 0:
            skipLines -= 1
            continue

        # find the start of a paragraph
        if re.search(schema["general"]["blank_line"], lines[i], re.UNICODE) is not None or i == 0:
            
            # because we culled double empty lines, we know the next line is a paragraph start... find the end
            newParagraph = u''
            for j in xrange(i+1, len(lines)-1):
                
                if re.search(schema["general"]["blank_line"], lines[j], re.UNICODE) is not None:
                    # we found the end
                    break
                else:
                    newParagraph += lines[j].strip(u'\n\r\f').strip() + u' '

            outputLinesParagraphed.append(newParagraph + u'\n')
            skipLines = j-i-1
    
    return outputLinesParagraphed
    
def initial_cleanup(schema, lines):
    """
        Given a schema and set of lines, remove page breaks, the footer, and repeating blank lines.
    """
    outputLines = []
    for i in xrange(0, len(lines)-1):
        printIt = True
        if re.search(schema["general"]["page_break"], lines[i], re.UNICODE) is not None:
            printIt = False
        
        for s in schema["footer"]["repeating"]:
            if re.search(s, lines[i], re.UNICODE) is not None:
                printIt = False
        
        for s in schema["footer"]["page_numbers"]:
            if re.search(s, lines[i], re.UNICODE) is not None:
                printIt = False

        if i > 0 and len(outputLines) > 0:
            if re.search(schema["general"]["blank_line"], lines[i], re.UNICODE) is not None and re.search(schema["general"]["blank_line"], outputLines[-1], re.UNICODE) is not None:
                printIt = False

        if printIt:
            outputLines.append(lines[i])
            
    return outputLines
                
def schemize_footer_header(schema, lines):
    """
        Given a schema JSON object and a document (a list of text lines),
        it will detect page breaks and then build the header/footer schema.
    """
    lookLength = 10
    page = 1
    pageOffset = None
    tempSchema = ur""
    newPageSchema = ur""
    potentials = {}     # key = a line of text in the footer, value = instance count across pages
    minCount = 10       # minimum number of instances to count as a repetition
    
    for i in xrange(0, len(lines)-1):
    
        match = re.search(schema["general"]["page_break"], lines[i], re.UNICODE)
        if match:
            # found a page break, so loop backward X (= lookLength) lines and look for:
            # (a) potential page numbers
            # (b) other repeating useless elements (like version numbers, esoteric codes, etc.)
            
            for j in xrange(1, lookLength):
                if len(lines[i-j]) > 0:
                    p, parts = extract_numeric(lines[i-j])
                
                    if lines[i-j] in potentials:
                        potentials[lines[i-j]] += 1
                        
                    elif p is not None and newPageSchema == ur"":
                        # need to: first time, we save the page offset and the schema temporarily
                        #   second time, if the page offset still holds, we can save the schema permanently and stop looking for it
                        
                        # if the number extracted is similar enough to our guessed page number, let's save the schema
                        if abs(p - page) < 10 and pageOffset is None:  
                            pageOffset = p - page

                            tempSchema = ur"^"
                            for part in parts:
                                try:
                                    int(part)
                                    tempSchema += ur"\d+ *"
                                except:
                                    tempSchema += part + ur" *"
                            
                            tempSchema += ur"(\n|\r|\f)"
                            
                        elif (p - page) == pageOffset:
                            newPageSchema = tempSchema
                                
                    else:
                        potentials[lines[i-j]] = 1
                
            page = page + 1
                
    # save the page number schema
    if newPageSchema != ur"":
        schema["footer"]["page_numbers"].append(newPageSchema)
        
    # save the schema for repeating elements
    schema["footer"]["repeating"] = []
    for key, val in potentials.iteritems():
        if val > minCount and ord(key[0]) != ord('\r') and ord(key[0]) != ord('\n') and ord(key[0]) != ord(' '):
            
            cleanKey = ur"^" + key.strip() + ur" *(\n|\r|\f)"
        
            if "repeating" in schema["footer"]:
                schema["footer"]["repeating"].append(cleanKey)
            else:
                schema["footer"]["repeating"] = [cleanKey]

def extract_numeric(line):
    """
        Given a string, break it down into components (space delimited) and see if there are any standalone numerical values.
        Intended to take a string and detect page numbers within it.
        For example, extract_numeric(" -- 27 -- ") = 27
    """
    parts = line.strip().split(u" ")
    for part in parts:
        try:
            int(part)
            return int(part), parts
        except:
            continue

    return None, None
            
def usage():
    print "\n*** HELP ***"
    print "TBD"
    
if __name__ == '__main__':
    main(sys.argv[1:])