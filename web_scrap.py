import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import sys


def parse(content):
    parm_dict = {}
    for tag in content:
        date = tag.find('a')
        date = str(date).rsplit('#')[1][1:11]

        min_temp = tag.find("dd", {'class': 'min'})
        if min_temp:
            min_temp = (re.search("\d?\d", str(min_temp))).group()

        max_temp = tag.find("dd", {'class': 'max'})
        if max_temp:
            max_temp = (re.search("\d?\d", str(max_temp))).group()

        rain_amt = tag.find("dd", {'class': 'amt'})
        if rain_amt:
            rain_amt = re.findall("\>(.*?)\<", str(rain_amt))

        rain_prob = tag.find("dd", {'class': 'pop'})
        if rain_prob:
            rain_prob = re.search("\d?\d%", str(rain_prob)).group()

        parm_dict[date] = [date, min_temp, max_temp, rain_amt, rain_prob]

    return parm_dict


## MAIN

df = pd.read_csv('/content/Nearest_stations.csv')

weather_parm = {}
for store, suburb, state in zip(df['store'], df['Suburb'], df['State Geo']):

  state = state.strip().lower()
  suburb = suburb.strip().replace(' ', '-').lower()

  url = 'http://www.bom.gov.au/places/' + state + '/' + suburb

  print(url)

  raw_data = requests.get(url)

  # print(raw_data.status_code)

  if raw_data.status_code != 200:
    print('failed at fetch')
    continue

  html = BeautifulSoup(raw_data.content, 'html.parser')

  content = html.find_all("dl", {'class':'forecast-summary'})
  # print(content)
  # break
  # print(content)

  weather_parm[store] = parse(content)


out_df = pd.DataFrame(weather_parm).reset_index()
print(out_df.head())



