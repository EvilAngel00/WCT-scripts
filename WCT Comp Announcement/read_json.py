import json

with open('states_list.json') as json_data:
    d = json.load(json_data)

iso2country_continent = {}

for item in d['states_lists']:
    for state in item['states']:
        iso2country_continent[state['iso2']] = (state['name'], state['continent_id'][1:])
       