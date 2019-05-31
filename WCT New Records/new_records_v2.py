################################################
# WCT Reddit Weekly Records Summary            #
#                                              #
# Author: Rui Reis                             #
# Contact: rreis@worldcubeassociation.org      #
# Date Created: 31 May 2019                    #
# Last Version: 31 May 2019                    #
################################################

import requests, datetime, os, urllib2, zipfile, pprint, json, codecs
# pip install ruamel.yaml
import ruamel.yaml as yaml
# pip install pytz
import pytz
# pip install python-dateutil
from dateutil.parser import parse as parsedate
from read_json import *

def downloadFile(url):
    file_name = url.split('/')[-1]
    u = urllib2.urlopen(url)
    f = open(file_name, 'wb')
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    print "Downloading: %s Bytes: %s" % (file_name, file_size)

    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break

        file_size_dl += len(buffer)
        f.write(buffer)
        status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        status = status + chr(8)*(len(status)+1)
        print status,

    f.close()

def extract(zip_file, destination):
    print "Extracting files..."
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(destination)
    print "Extraction complete!"


def getLatestComps(export_folder, days_ago):
    today = datetime.datetime.today()
    year = int(today.strftime('%Y'))
    month = int(today.strftime('%m'))
    day = int(today.strftime('%d'))

    week_ago = today - datetime.timedelta(days=7)
    year_week_ago = int(week_ago.strftime('%Y'))
    month_week_ago = int(week_ago.strftime('%m'))
    day_week_ago = int(week_ago.strftime('%d'))    

    comps = []
    with open(export_folder + "/WCA_export_Competitions.tsv") as f:
        next(f)
        for line in f:
            line = line.split('\t')
            if((int(line[5]) in range(year_week_ago, year+1)) and (int(line[6]) in range(month_week_ago, month+1)) and (int(line[7]) in range(day_week_ago, day+1))):
                comps.append(line[0])
    f.close()
    
    comps_without_results = [line.rstrip('\n') for line in open('comps_without_results.txt')][:-1]
    comps = list(set(comps + comps_without_results))
    
    return comps

def saveComps(comps):
    f = open('comps_without_results.txt', 'w+')
    for comp in comps:
        f.write(comp + '\n')
    f.close()

def getNewRecords(export_folder, comps):
    records = []
    comps_with_results = []
    with open(export_folder + "/WCA_export_Results.tsv") as f:
        for line in f:
            line = line.split('\t')
            if(line[0] in comps):
                comps_with_results.append(line[0])
                if(line[15].endswith('R') or line[16].rstrip().endswith('R')):
                    records.append(line)
    
    comps_with_results = list(set(comps_with_results))
    comps_without_results = [comp for comp in comps if comp not in comps_with_results]
    saveComps(comps_without_results)
    
    return records

def formatNewRecords(new_records):
    record_type_continent = {'AfR': 'Africa', 'AsR': 'Asia', 'ER': 'Europe', 'NAR': 'North America', 'SAR': 'South America', 'OcR': 'Oceania'}
    formatted_new_records = []
    
    for record in new_records:
        if(record[15] == 'WR'):
            formatted_new_records.append([record[6], record[1], record[4], "Single", record[15], 'World'])
        if(record[16].rstrip() == 'WR'):
            formatted_new_records.append([record[6], record[1], record[5], "Average", record[16].rstrip(), 'World'])
        if(record[15] in record_type_continent):
            formatted_new_records.append([record[6], record[1], record[4], "Single", "CR", record_type_continent[record[15]]])
        if(record[16].rstrip() in record_type_continent):
            formatted_new_records.append([record[6], record[1], record[5], "Average", "CR", record_type_continent[record[16].rstrip()]])
        if(record[15] == 'NR'):
            formatted_new_records.append([record[6], record[1], record[4], "Single", record[15], record[8]])
        if(record[16].rstrip() == 'NR'):
            formatted_new_records.append([record[6], record[1], record[5], "Average", record[16].rstrip(), record[8]])

    return sortNewRecords(formatted_new_records)
    
def sortNewRecords(formatted_new_records):
    record_sort_order = {"WR": 0, "CR": 1, "NR": 2}
    event_sort_order = {"333":0, "222":1, "444":2, "555":3, "666":4, "777":5, "333bf":6, "333fm":7, "333oh":8, "333ft":9, "clock":10, "minx":11, "pyram":12, "skewb":13, "sq1":14, "444bf":15, "555bf":16, "333mbf":17}
    type_sort_order = {"Single":0, "Average":1}
    
    formatted_new_records.sort(key=lambda x: (record_sort_order[x[4]], x[5], event_sort_order[x[1]], type_sort_order[x[3]]))
    
    return formatted_new_records

# Returns dictionaries for events with:
# event_id = event_name for events
def getEvents(export_folder):
    events = []
    with open(export_folder + "/WCA_export_Events.tsv") as f:
        for line in f:
            line = line.split('\t')
            events.append(line)

    events_dict = {}
    for event in events:
        events_dict[event[0]] = event[1]

    return events_dict
    
# Get a formatted text version of the result
# i.e. moves for FMC, seconds if <1:00, minutes otherwise,
# correct MBLD representation.
def getFormattedTime(time, event, single_avg):
    if event != '3x3x3 Fewest Moves' and event != '3x3x3 Multi-Blind':
        time = int(time)
        s, cs = divmod(time, 100)
        m, s = divmod(s, 60)
        if m == 0:
            ret = "%d.%02d seconds" % (s, cs)
        else:
            ret = "%d:%02d.%02d minutes" % (m, s, cs)
    elif event == '3x3x3 Fewest Moves':
        if single_avg == 'Single':
            ret = time + " moves"
        else:
            ret = str(float(time)/100) + " moves"
    elif event == '3x3x3 Multi-Blind':
        difference = 99 - int(time[0:2])
        mbf_time = int(time[2:7])
        m, s = divmod(mbf_time, 60)
        h, m = divmod(m, 100)
        mbf_time = "%d:%02d minutes" % (m, s)
        missed = int(time[7:9])
        solved = difference + missed
        attempted = solved + missed
        ret = str(solved) + "/" + str(attempted) + " in " + mbf_time

    return ret

# Get the formatted line in unicode to write to the file
def getLine(record, events_dict):
    record_types = {'Asia': 'AsR', 'Africa': 'AfR', 'Europe': 'ER', 'North America': 'NAR', 'South America': 'SAR', 'Oceania': 'OcR', 'World': 'World Record'}
    name = record[0]
    event = events_dict[record[1]]
    time = record[2]
    single_avg = record[3]
    if record[5] in record_types:
        r_type = record_types[record[5]]
    else:
        r_type = "NR"
    
    str = "* " + event + " " + r_type + " " + single_avg + " of " + getFormattedTime(time, event, single_avg) + " by " + name + "\n"

    return unicode(str, 'ISO-8859-1')

# Write to a file with reddit formatting (markdown)
def writeRecords(new_records, events_dict):
    if not os.path.exists('reddit'):
        os.makedirs('reddit')
    now = datetime.datetime.now()
    week_ago = now - datetime.timedelta(days=7)
    filename = 'reddit/' + now.strftime("%Y-%m-%d") + " Records.txt"
    print 'Writing ./' + filename + '...'
    f = codecs.open(filename, "w", 'ISO-8859-1')
    
    # Write the headers
    f.write(u'WCA Records Thread for Week ' + str(week_ago.isocalendar()[1]) + u' of ' + now.strftime("%Y"))
    f.write(u'\n')
    f.write(u'\n')

    template = [u'Hi /r/cubers!', u'\n\n', u'Here is the list of new records since Tuesday ' + week_ago.strftime("%Y-%m-%d") + u'.', u'\n\n']
    
    f.writelines(template)

    current_record_type = ""
    current_continent = ""
    current_country = ""
    for record in new_records:
        if record[4] != current_record_type and record[4] == "WR":
            current_record_type = "WR"
            f.write(u'# World Records\n\n')
        elif record[4] != current_record_type and record[4] == "CR":
            current_record_type = "CR"
            current_continent = record[5]
            f.write(u'\n# Continental Records\n\n')
            f.write(u'**' + current_continent + u'**' + u'\n\n')
        elif record[4] == current_record_type and record[4] == "CR" and record[5] != current_continent:
            current_continent = record[5]
            f.write(u'\n**' + current_continent + u'**' + u'\n\n')
        elif record[4] != current_record_type and record[4] == "NR":
            current_record_type = "NR"
            current_country = record[5]
            f.write(u'\n# National Records\n\n')
            f.write(u'**' + current_country + u'**' + u'\n\n')
        elif record[4] == current_record_type and record[4] == "NR" and record[5] != current_country:
            current_country = record[5]
            f.write(u'\n**' + current_country + u'**' + u'\n\n')
        
        f.write(getLine(record, events_dict))
        
    f.close()
    print "File written!"

# Permalink WCA database export 
url = 'https://www.worldcubeassociation.org/results/misc/WCA_export.tsv.zip'
file = 'WCA_export.tsv.zip'
export_folder = 'WCA_export'
json_folder = 'records_json'
utc = pytz.UTC

# Get server file modified date
r = requests.head(url)
url_time = r.headers['last-modified']
url_date = parsedate(url_time)

# Check if export exists locally
if os.path.isfile(file):
    file_time = datetime.datetime.fromtimestamp(os.path.getmtime(file))
# If not, download and write records to json
else:
    print "WCA Database Export doesn't exist - Downloading now"
    downloadFile(url)
    file_time = datetime.datetime.fromtimestamp(os.path.getmtime(file))
    extract(file, export_folder)

# If the database is newer, download and compare to local records
if url_date > utc.localize(file_time):
    print "Local WCA Database Export is older than server - Downloading now"
    downloadFile(url)
    extract(file, export_folder)
else:
    print "Local WCA Database Export is the latest version"
    comps = getLatestComps(export_folder, 7)
    new_records = getNewRecords(export_folder, comps)
    formatted_new_records = formatNewRecords(new_records)
    events_dict = getEvents(export_folder)
    writeRecords(formatted_new_records, events_dict)

