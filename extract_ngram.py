import os, sys
import shelve
from collections import defaultdict

import MySQLdb as mdb

import ConfigParser
Config = ConfigParser.ConfigParser()
Config.read('jstor.cnf')

con = None
try:
        con = mdb.connect('localhost', Config.get('database', 'username'), Config.get('database', 'password'), Config.get('database', 'database'));

        cur = con.cursor()
        cur.execute("SELECT VERSION()")

        data = cur.fetchone()
        print "Database version : %s " % data

except mdb.Error, e:
        print "Error %d: %s" % (e.args[0],e.args[1])
        sys.exit(1)

cur = con.cursor()

try:
    discipline = sys.argv[1] + '-discipline'
    year = sys.argv[2]
    # cur.execute("SELECT DISTINCT r.doi FROM j_reviews r JOIN j_disciplines d ON (r.j_review_id = d.j_review_id) WHERE r.language = 'eng' AND r.num_reviewed_works = 1 AND r.reviewed_works != '' AND r.reviewed_works IS NOT NULL AND d.discipline = %s AND r.year = %s;", (discipline, int(year)))

    # joins with amazon data (only things in both)
    cur.execute("SELECT DISTINCT r.doi, tim.amazon_id FROM j_reviews r JOIN j_disciplines d ON (r.j_review_id = d.j_review_id) JOIN title_id_map tim ON (r.reviewed_works_hash = tim.title_hash) JOIN a_reviews ar ON (tim.amazon_id = ar.amazon_id) WHERE r.language = 'eng' AND r.num_reviewed_works = 1 AND r.reviewed_works != '' AND r.reviewed_works IS NOT NULL AND d.discipline = %s AND r.year = %s;", (discipline, int(year)))

    rowcount = cur.rowcount
    if rowcount == 0:
        print "No records found for %s (%s)" % (discipline, year)
except mdb.Error, e:
        print "Error %d: %s" % (e.args[0],e.args[1])
        sys.exit(1)

which_ngram = sys.argv[3]

print "Going after %s of %s (%s)" % (which_ngram, discipline, year)

dataDir = Config.get('files', 'datadir')
if dataDir[-1] != '/': dataDir = dataDir + '/' # ensure trailing slash

ngramDir = dataDir + which_ngram + '/'
outfile = "%sextracts/%s-%s-%s.txt" % (dataDir, discipline, year, which_ngram)

dois = set([])
doi_amazon_id_map = {}
for i in range(rowcount):
    row = cur.fetchone()
    dois.add(row[0])
    if len(row) > 1: # allow for not joining with the amazon id
        doi_amazon_id_map[row[0]] = row[1]

print "Looking for %s DOIs" % len(dois)

o = open(outfile, 'wb')
i=0
dois_found=set([])
for part in os.listdir(ngramDir):
    f = open(ngramDir + part, 'rb')
    for line in f.readlines():
        i+=1
        doi = line[1:].split()[0]
        if doi in dois:
            dois_found.add(doi)
            if len(doi_amazon_id_map): # allow for not joining with the amazon id
                o.write(doi_amazon_id_map[doi] + "\t" + line.replace('"', ''))
            else:
                o.write(line.replace('"', ''))
    f.close()
o.close()
print 'Found %s DOIs' % len(dois_found)
print 'Checked %s lines' % i

