################################################
# WCT Reddit Weekly Records Summary            #
#                                              #
# Author: Rui Reis                             #
# Contact: rreis@worldcubeassociation.org      #
# Date Created: 11 December 2018               #
# Last Version: 14 December 2018               #
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

# Returns dictionaries for people and events with:
# WCA_id = [name, country] for persons
# event_id = event_name for events
def getPersonsEvents(export_folder):
    persons = []
    with open(export_folder + "/WCA_export_Persons.tsv") as f:
        for line in f:
            line = line.split('\t')
            persons.append(line)

    persons_dict = {}
    for person in persons:
        # If person has changed citizenship, only keeps the last one
        if person[1] == "1":
            persons_dict[person[0]] = {'name': person[2], 'countryId': person[3]}

    events = []
    with open(export_folder + "/WCA_export_Events.tsv") as f:
        for line in f:
            line = line.split('\t')
            events.append(line)

    events_dict = {}
    for event in events:
        events_dict[event[0]] = event[1]

    return persons_dict, events_dict

# Get a dictionary with the records separated by country/continent/World 
# and Single/Average
def getAllRecords(export_folder, persons_dict):
    single_records_by_country, single_records_by_continent, single_records_world = updateRecords(export_folder, 's', persons_dict)
    average_records_by_country, average_records_by_continent, average_records_world = updateRecords(export_folder, 'a', persons_dict)

    all_records = {'single_records_by_country': single_records_by_country, 'single_records_by_continent': single_records_by_continent, 'single_records_world': single_records_world, 'average_records_by_country': average_records_by_country, 'average_records_by_continent': average_records_by_continent, 'average_records_world': average_records_world}

    return all_records

# Update the local JSON records with the most recent records
def updateRecords(export_folder, type, persons_dict):
    if type == 's':
        file = export_folder + "/WCA_export_RanksSingle.tsv"
    elif type == 'a':
        file = export_folder + "/WCA_export_RanksAverage.tsv"

    ranks = []
    with open(file) as f:
        for line in f:
            line = line.split('\t')
            if line[0] != 'personId':
                ranks.append(line)

    records_by_country = {}
    records_by_continent = {}
    records_world = {}

    for result in ranks:
        person_id = result[0]
        if person_id in persons_dict:
            person = persons_dict[person_id]
            country = person['countryId']
            continent = countryId_continent[country][1]
            event = result[1]
            best = result[2]

            # Get best records per country
            if country in records_by_country:
                current_records = records_by_country[country]
                if event in current_records:
                    # If record is better, replace old one
                    if int(current_records[event][0][1]) > int(best):
                        current_records[event] = [[person_id, best]]
                    # If record is tied, append to list
                    elif int(current_records[event][0][1]) == int(best):
                        current_records[event] = current_records[event] + [[person_id, best]]
                else:
                    current_records[event] = [[person_id, best]]

            else:
                records_by_country[country] = {}
                records_by_country[country][event] = [[person_id, best]]

            # Get best records per continent
            if continent in records_by_continent:
                current_records = records_by_continent[continent]
                if event in current_records:
                    if int(current_records[event][0][1]) > int(best):
                        current_records[event] = [[person_id, best]]
                    elif int(current_records[event][0][1]) == int(best):
                        current_records[event] = current_records[event] + [[person_id, best]]
                else:
                    current_records[event] = [[person_id, best]]

            else:
                records_by_continent[continent] = {}
                records_by_continent[continent][event] = [[person_id, best]]

            # Get World Records
            if event in records_world:
                if int(records_world[event][0][1]) > int(best):
                    records_world[event] = [[person_id, best]]
                elif int(records_world[event][0][1]) == int(best):
                    records_world[event] = records_world[event] + [[person_id, best]]
            else:
                records_world[event] = [[person_id, best]]

    return records_by_country, records_by_continent, records_world

# Write the records to JSON files
def writeJSON(dict_of_records, json_folder):
    print "Writing records to ./"+ json_folder
    if not os.path.exists(json_folder):
        os.makedirs(json_folder)
    for record in dict_of_records.keys():
        with open(json_folder + '/' + record + '.json', 'w') as fp:
            json.dump(dict_of_records[record], fp)
    print "Records written!"

# Compare records from new export with local JSON files
def compareRecords(records_json_folder, export_folder, persons_dict):
    record_names = ["single_records_by_country", "single_records_by_continent", "single_records_world", "average_records_by_country", "average_records_by_continent", "average_records_world"]
    all_records_past = {}

    for record_name in record_names:
        with open('./' + records_json_folder + '/' + record_name + '.json', 'r') as fp:
            data = yaml.safe_load(fp)
        all_records_past[record_name] = data

    all_records_new = getAllRecords(export_folder, persons_dict)

    # Dictionary of differences in records
    # Schema: World/Continental/National -> Continent/Country -> Event -> [['WCA_id', 'time', 'tie/no_tie', 'Single/Average'], ...]
    all_records_diff = {}

    wr_type = "single_records_world"
    for event in all_records_new[wr_type].keys():
        if sorted(all_records_new[wr_type][event]) != sorted(all_records_past[wr_type][event]):
            if len(all_records_new[wr_type][event]) > 1:
                    current_wrs = set(tuple(x) for x in all_records_new[wr_type][event])
                    past_wrs = set(tuple(x) for x in all_records_past[wr_type][event])
                    new_records = list(list(x) for x in current_wrs - past_wrs)
                    new_records = [x + ["tie"] for x in new_records]
            else:
                new_records = [x + ["no_tie"] for x in all_records_new[wr_type][event]]
            if "World" not in all_records_diff:
                all_records_diff["World"] = {}
            if event not in all_records_diff["World"]:
                all_records_diff["World"][event] = []
            all_records_diff["World"][event] = all_records_diff["World"][event] + [x + ["Single"] for x in new_records]

    wr_type = "average_records_world"
    for event in all_records_new[wr_type].keys():
        if sorted(all_records_new[wr_type][event]) != sorted(all_records_past[wr_type][event]):
            if len(all_records_new[wr_type][event]) > 1:
                    current_wrs = set(tuple(x) for x in all_records_new[wr_type][event])
                    past_wrs = set(tuple(x) for x in all_records_past[wr_type][event])
                    new_records = list(list(x) for x in current_wrs - past_wrs)
                    new_records = [x + ["tie"] for x in new_records]
            else:
                new_records = [x + ["no_tie"] for x in all_records_new[wr_type][event]]
            if "World" not in all_records_diff:
                all_records_diff["World"] = {}
            if event not in all_records_diff["World"]:
                all_records_diff["World"][event] = []
            all_records_diff["World"][event] = all_records_diff["World"][event] + [x + ["Average"] for x in new_records]

    cr_type = "single_records_by_continent"
    for continent in all_records_new[cr_type].keys():
        for event in all_records_new[cr_type][continent].keys():
            if sorted(all_records_new[cr_type][continent][event]) != sorted(all_records_past[cr_type][continent][event]):
                new = set(["lala"])
                if "World" in all_records_diff and event in all_records_diff["World"]:
                    current = set(tuple(x) for x in all_records_new[cr_type][continent][event])
                    past = set(tuple(x) for x in map(lambda x: [x[0], x[1]], all_records_diff["World"][event]))
                    new = current - past
                if len(new) == 0:
                    print "CR single is also a WR!"
                else:
                    if len(all_records_new[cr_type][continent][event]) > 1:
                            current_crs = set(tuple(x) for x in all_records_new[cr_type][continent][event])
                            past_crs = set(tuple(x) for x in all_records_past[cr_type][continent][event])
                            new_records = list(list(x) for x in current_crs - past_crs)
                            new_records = [x + ["tie"] for x in new_records]
                    else:
                        new_records = [x + ["no_tie"] for x in all_records_new[cr_type][continent][event]]
                    if "Continental" not in all_records_diff:
                        all_records_diff["Continental"] = {}
                    if continent not in all_records_diff["Continental"]:
                        all_records_diff["Continental"][continent] = {}
                    if event not in all_records_diff["Continental"][continent]:
                        all_records_diff["Continental"][continent][event] = []
                    all_records_diff["Continental"][continent][event] = all_records_diff["Continental"][continent][event] + [x + ["Single"] for x in new_records]

    cr_type = "average_records_by_continent"
    for continent in all_records_new[cr_type].keys():
        for event in all_records_new[cr_type][continent].keys():
            if sorted(all_records_new[cr_type][continent][event]) != sorted(all_records_past[cr_type][continent][event]):
                new = set(["lala"])
                if "World" in all_records_diff and event in all_records_diff["World"]:
                    current = set(tuple(x) for x in all_records_new[cr_type][continent][event])
                    past = set(tuple(x) for x in map(lambda x: [x[0], x[1]], all_records_diff["World"][event]))
                    new = current - past
                    print "-----"
                    print current
                    print past
                    print new
                    print "-----"
                if len(new) == 0:
                    print "CR average is also a WR!"
                else:
                    if len(all_records_new[cr_type][continent][event]) > 1:
                            current_crs = set(tuple(x) for x in all_records_new[cr_type][continent][event])
                            past_crs = set(tuple(x) for x in all_records_past[cr_type][continent][event])
                            new_records = list(list(x) for x in current_crs - past_crs)
                            new_records = [x + ["tie"] for x in new_records]
                    else:
                        new_records = [x + ["no_tie"] for x in all_records_new[cr_type][continent][event]]
                    if "Continental" not in all_records_diff:
                        all_records_diff["Continental"] = {}
                    if continent not in all_records_diff["Continental"]:
                        all_records_diff["Continental"][continent] = {}
                    if event not in all_records_diff["Continental"][continent]:
                        all_records_diff["Continental"][continent][event] = []
                    all_records_diff["Continental"][continent][event] = all_records_diff["Continental"][continent][event] + [x + ["Average"] for x in new_records]

    nr_type = "single_records_by_country"
    for country in all_records_new[nr_type].keys():
        for event in all_records_new[nr_type][country].keys():
            if country not in all_records_past[nr_type] or event not in all_records_past[nr_type][country] or sorted(all_records_new[nr_type][country][event]) != sorted(all_records_past[nr_type][country][event]):
                continent = countryId_continent[country][1]
                new_wr = set(["lala"])
                new_cr = set(["lala"])
                if "World" in all_records_diff and event in all_records_diff["World"]:
                    current = set(tuple(x) for x in all_records_new[nr_type][country][event])
                    past = set(tuple(x) for x in map(lambda x: [x[0], x[1]], all_records_diff["World"][event]))
                    new_wr = current - past
                    if len(new_wr) == 0:
                        print "NR single is also a WR!"
                if "Continental" in all_records_diff and continent in all_records_diff["Continental"] and event in all_records_diff["Continental"][continent]:
                    current = set(tuple(x) for x in all_records_new[nr_type][country][event])
                    past = set(tuple(x) for x in map(lambda x: [x[0], x[1]], all_records_diff["Continental"][continent][event]))
                    new_cr = current - past
                    if len(new_cr) == 0:
                        print "NR single is also a CR!"
                if len(new_wr) != 0 and len(new_cr) != 0:
                    if len(all_records_new[nr_type][country][event]) > 1:
                            current_nrs = set(tuple(x) for x in all_records_new[nr_type][country][event])
                            past_nrs = set(tuple(x) for x in all_records_past[nr_type][country][event])
                            new_records = list(list(x) for x in current_nrs - past_nrs)
                            new_records = [x + ["tie"] for x in new_records]
                    else:
                        new_records = [x + ["no_tie"] for x in all_records_new[nr_type][country][event]]
                    if "National" not in all_records_diff:
                        all_records_diff["National"] = {}
                    if country not in all_records_diff["National"]:
                        all_records_diff["National"][country] = {}
                    if event not in all_records_diff["National"][country]:
                        all_records_diff["National"][country][event] = []
                    all_records_diff["National"][country][event] = all_records_diff["National"][country][event] + [x + ["Single"] for x in new_records]

    nr_type = "average_records_by_country"
    for country in all_records_new[nr_type].keys():
        for event in all_records_new[nr_type][country].keys():
            if country not in all_records_past[nr_type] or event not in all_records_past[nr_type][country] or sorted(all_records_new[nr_type][country][event]) != sorted(all_records_past[nr_type][country][event]):
                continent = countryId_continent[country][1]
                new_wr = set(["lala"])
                new_cr = set(["lala"])
                if "World" in all_records_diff and event in all_records_diff["World"]:
                    current = set(tuple(x) for x in all_records_new[nr_type][country][event])
                    past = set(tuple(x) for x in map(lambda x: [x[0], x[1]], all_records_diff["World"][event]))
                    new_wr = current - past
                    if len(new_wr) == 0:
                        print "NR average is also a WR!"
                if "Continental" in all_records_diff and continent in all_records_diff["Continental"] and event in all_records_diff["Continental"][continent]:
                    current = set(tuple(x) for x in all_records_new[nr_type][country][event])
                    past = set(tuple(x) for x in map(lambda x: [x[0], x[1]], all_records_diff["Continental"][continent][event]))
                    new_cr = current - past
                    if len(new_cr) == 0:
                        print "NR average is also a CR!"
                if len(new_wr) != 0 and len(new_cr) != 0:
                    if len(all_records_new[nr_type][country][event]) > 1:
                            current_nrs = set(tuple(x) for x in all_records_new[nr_type][country][event])
                            past_nrs = set(tuple(x) for x in all_records_past[nr_type][country][event])
                            new_records = list(list(x) for x in current_nrs - past_nrs)
                            new_records = [x + ["tie"] for x in new_records]
                    else:
                        new_records = [x + ["no_tie"] for x in all_records_new[nr_type][country][event]]
                    if "National" not in all_records_diff:
                        all_records_diff["National"] = {}
                    if country not in all_records_diff["National"]:
                        all_records_diff["National"][country] = {}
                    if event not in all_records_diff["National"][country]:
                        all_records_diff["National"][country][event] = []
                    all_records_diff["National"][country][event] = all_records_diff["National"][country][event] + [x + ["Average"] for x in new_records]

    print all_records_diff
    return all_records_diff

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
def getLine(name, event, time, single_avg, record_type, tie, fb_reddit):
    record_types = {'Asia': 'AsR', 'Africa': 'AfR', 'Europe': 'ER', 'North America': 'NAR', 'South America': 'SAR', 'Oceania': 'OcR', 'World': 'World Record'}
    if record_type in record_types:
        r_type = record_types[record_type]
    else:
        r_type = "NR"
    if tie == "tie":
        #sub = "tied the "
        sub = " (tied)"
    else:
        #sub = "set a new "
        sub = ""
    head = ""
    if fb_reddit == "reddit":
        head = "* "
    #str = head + name + " has " + sub + r_type + " " + single_avg + " in " + event + " with a result of " + getFormattedTime(time, event, single_avg) + "!\n"
    str = head + event + " " + r_type + " " + single_avg + sub + " of " + getFormattedTime(time, event, single_avg) + " by " + name + "\n"

    return unicode(str, 'ISO-8859-1')

# Write to a file with reddit formatting (markdown)
def writeRecordsReddit(all_records_diff, persons_dict, events_dict):
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

    if "World" in all_records_diff:
        f.write(u'# World Records\n\n')
        for event in all_records_diff["World"]:
            for record in all_records_diff["World"][event]:
                f.write(getLine(persons_dict[record[0]]['name'], events_dict[event], record[1], record[3], "World", record[2], "reddit"))
    f.write(u'\n')

    if "Continental" in all_records_diff:
        f.write(u'# Continental Records\n')
        for continent in sorted(all_records_diff["Continental"].keys()):
            f.write(u'\n**' + continent + u'**' + u'\n\n')
            for event in all_records_diff["Continental"][continent]:
                for record in all_records_diff["Continental"][continent][event]:
                    f.write(getLine(persons_dict[record[0]]['name'], events_dict[event], record[1], record[3], continent, record[2], "reddit"))
    f.write(u'\n')

    if "National" in all_records_diff:
        f.write(u'# National Records\n')
        for country in sorted(all_records_diff["National"].keys()):
            f.write(u'\n**' + country + u'**' + u'\n\n')
            for event in all_records_diff["National"][country]:
                for record in all_records_diff["National"][country][event]:
                    f.write(getLine(persons_dict[record[0]]['name'], events_dict[event], record[1], record[3], country, record[2], "reddit"))
    f.close()
    print "File written!"

# Write to a file with plain text formatting
def writeRecordsFacebook(all_records_diff, persons_dict, events_dict):
    if not os.path.exists('facebook'):
        os.makedirs('facebook')
    now = datetime.datetime.now()
    week_ago = now - datetime.timedelta(days=7)
    filename = 'facebook/' + now.strftime("%Y-%m-%d") + " Records.txt"
    print 'Writing ./' + filename + '...'
    f = codecs.open(filename, "w", 'ISO-8859-1')

    # Write the headers
    f.write(u'WCA Records for Week ' + str(week_ago.isocalendar()[1]) + u' of ' + now.strftime("%Y"))
    f.write(u'\n')
    f.write(u'\n')

    template = [u'Dear community, here is the list of new records since Tuesday ' + week_ago.strftime("%Y-%m-%d") + u'.', u'\n\n']
    
    f.writelines(template)

    if "World" in all_records_diff:
        f.write(u'World Records\n\n')
        for event in all_records_diff["World"]:
            for record in all_records_diff["World"][event]:
                f.write(getLine(persons_dict[record[0]]['name'], events_dict[event], record[1], record[3], "World", record[2], "facebook"))
    f.write(u'\n')

    if "Continental" in all_records_diff:
        f.write(u'Continental Records\n')
        for continent in all_records_diff["Continental"]:
            f.write(u'\n' + continent + u'\n\n')
            for event in all_records_diff["Continental"][continent]:
                for record in all_records_diff["Continental"][continent][event]:
                    f.write(getLine(persons_dict[record[0]]['name'], events_dict[event], record[1], record[3], continent, record[2], "facebook"))
    f.write(u'\n')

    if "National" in all_records_diff:
        f.write(u'National Records\n')
        for country in all_records_diff["National"]:
            f.write(u'\n' + country + u'\n\n')
            for event in all_records_diff["National"][country]:
                for record in all_records_diff["National"][country][event]:
                    f.write(getLine(persons_dict[record[0]]['name'], events_dict[event], record[1], record[3], country, record[2], "facebook"))

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
    persons_dict, events_dict = getPersonsEvents(export_folder)
    all_records = getAllRecords(export_folder, persons_dict)
    writeJSON(all_records, json_folder)

# If the database is newer, download and compare to local records
if url_date > utc.localize(file_time):
    print "Local WCA Database Export is older than server - Downloading now"
    downloadFile(url)
    extract(file, export_folder)
    persons_dict, events_dict = getPersonsEvents(export_folder)
    all_records_diff = compareRecords(json_folder, export_folder, persons_dict)
    writeRecordsReddit(all_records_diff, persons_dict, events_dict)
    writeRecordsFacebook(all_records_diff, persons_dict, events_dict)
    all_records = getAllRecords(export_folder, persons_dict)
    writeJSON(all_records, json_folder)
else:
    print "Local WCA Database Export is the latest version"
    persons_dict, events_dict = getPersonsEvents(export_folder)
    all_records_diff = compareRecords(json_folder, export_folder, persons_dict)
    writeRecordsReddit(all_records_diff, persons_dict, events_dict)
    writeRecordsFacebook(all_records_diff, persons_dict, events_dict)
    all_records = getAllRecords(export_folder, persons_dict)
    writeJSON(all_records, json_folder)
