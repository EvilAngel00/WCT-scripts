import json

with open('states_list.json') as json_data:
    d = json.load(json_data)

iso2country_continent = {}
countryId_continent = {}

for item in d['states_lists']:
    for state in item['states']:
        iso2country_continent[state['iso2']] = (state['name'], state['continent_id'][1:])
        countryId_continent[state['id']] = (state['iso2'], state['continent_id'][1:])
