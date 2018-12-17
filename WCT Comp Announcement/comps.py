################################################
# WCT Reddit Weekly Competitions Announcement  #
#                                              #
# Author: Rui Reis                             #
# Contact: rreis@worldcubeassociation.org      #
# Date Created: 04 March 2018                  #
# Last Version: 14 December 2018               #
################################################

import requests, json, datetime, collections, io, os
from read_json import *

# Today's date
now = datetime.datetime.now()
# Date from 7 days ago, if we need comps announced for more time,
# change the number of days here
week_ago = now - datetime.timedelta(days=7)

# Create the new folder and file
if not os.path.exists("output"):
    os.makedirs("output")
f = io.open("./output/" + now.strftime("%Y-%m-%d") + " Competitions.txt", "w", encoding='utf16')

# Write the headers
f.write(u'WCA Competition Announcement Thread for Week ' + str(week_ago.isocalendar()[1]).decode('unicode-escape') + u' of ' + now.strftime("%Y").decode('unicode-escape'))
f.write(u'\n')
f.write(u'\n')

template = [u'Hi /r/cubers!', u'\n\n', 'Here is the list of competitions announced since Monday ' + week_ago.strftime("%Y-%m-%d") + u'. For more information please visit the corresponding websites :)', u'\n\n', u'Disclaimer: continents correspond to the WCA interpretation. The full list can be found [here](https://raw.githubusercontent.com/thewca/worldcubeassociation.org/master/WcaOnRails/config/wca-states.json).', u'\n\n', u'(Dates are year-month-day)', u'\n\n']

f.writelines(template)

# WCA API request
# Format: https://www.worldcubeassociation.org/api/v0/competitions?announced_after=yyyy-mm-dd
# If per_page isn't specified, we only get the first 25 comps
payload = {'announced_after': week_ago, 'per_page': 100}
r = requests.get('https://www.worldcubeassociation.org/api/v0/competitions', params=payload)

data = json.loads(r.text)
continents = {"Africa": [], "Asia": [], "Europe": [], "North America": [], "Oceania": [], "South America": [], "Multiple Cities": []}

# Separate the comps by continents
# If there is a key error it might be a multiple cities comp in a continent not added
# or comp['country_iso2'] == u'XM' needs to be added 2 lines below with XM replaced by the new key
for comp in data:
    if comp['country_iso2'] == u'XA' or comp['country_iso2'] == u'XM':
        continents["Multiple Cities"].append(("Multiple", comp['city'], comp['name'], comp['start_date'], comp['end_date'], comp['url']))
    else:
        continents[iso2country_continent[comp['country_iso2']][1]].append((iso2country_continent[comp['country_iso2']][0], 
																		comp['city'], comp['name'], comp['start_date'], comp['end_date'], comp['url']))                                                                        
continents = collections.OrderedDict(sorted(continents.items()))

# Write to file with the proper formatting
for continent in continents:
    if(len(continents[continent]) > 0):
        continents[continent].sort(key=lambda x: (x[0], x[1]))
        f.write("##" + continent.decode('unicode-escape') +"\n\n")
        f.write(u'Country|City|Name|Start Date|End Date|Website\n')
        f.write(u':--|:--|:--|:--|:--|:--\n')

        for comp in continents[continent]:
            f.write(comp[0] + u"|" + comp[1] + u"|" + comp[2]
                    + u"|" + comp[3] + u"|" + comp[4] + u"|" + u'[Link](' + comp[5] + u')\n')
    f.write(u"\n")
    
f.close() 