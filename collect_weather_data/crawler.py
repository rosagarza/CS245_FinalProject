import urllib.request as req
import json
import pandas as pd
from collect_data import *
import collections
import os, json

state_dict = {'Alabama': 0, 'Alaska': 1, 'Arizona': 2, 'Arkansas': 3, 'California': 4, 'Colorado': 5, 'Connecticut': 6, 'Delaware': 7, 'Florida': 8, 'Georgia': 9, 'Hawaii': 10, 'Idaho': 11, 'Illinois': 12, 'Indiana': 13, 'Iowa': 14, 'Kansas': 15, 'Kentucky': 16, 'Louisiana': 17, 'Maine': 18, 'Maryland': 19, 'Massachusetts': 20, 'Michigan': 21, 'Minnesota': 22, 'Mississippi': 23, 'Missouri': 24, 'Montana': 25, 'Nebraska': 26, 'Nevada': 27, 'New Hampshire': 28, 'New Jersey': 29, 'New Mexico': 30, 'New York': 31, 'North Carolina': 32, 'North Dakota': 33, 'Ohio': 34, 'Oklahoma': 35, 'Oregon': 36, 'Pennsylvania': 37, 'Rhode Island': 38, 'South Carolina': 39, 'South Dakota': 40, 'Tennessee': 41, 'Texas': 42, 'Utah': 43, 'Vermont': 44, 'Virginia': 45, 'Washington': 46, 'West Virginia': 47, 'Wisconsin': 48, 'Wyoming': 49}

def crawl(url, headers, requestData):
    request = req.Request(
        url=url, 
        headers=headers, 
        data=requestData.encode('utf-8')
    )
    with req.urlopen(request) as response:
        result = response.read().decode('utf-8')
    result = json.loads(result)
    #print(result)
    return result

def get_cities_lat_lng(file, city_state):
    # return the list of range of cities
    city_ranges = {}
    latlng = pd.read_csv(file, usecols=['city','state_id','lat','lng'])
    #city_state = collect_cities_with_states()
    for c in city_state:
        lat = latlng.loc[latlng['city']==c] #['lat'] #.at[1,'lat']
        lat = lat.loc[lat['state_id']==city_state[c]]['lat']
        lat = lat.values[0]
        lng = latlng.loc[latlng['city']==c]
        lng = lng.loc[lng['state_id']==city_state[c]]['lng']
        lng = lng.values[0]
        min_lat, max_lat = lat-1, lat+1
        min_lng, max_lng = lng-1, lng+1
        city_ranges[c] = [min_lng,min_lat,max_lng,max_lat]
    return city_ranges

def request_stid_each_city(city_ranges, city_state):
    if os.path.exists('cities_stids.json'):
        with open('cities_stids.json') as f:
            return json.load(f)
    cities_stids = collections.defaultdict(list)
    url = 'https://data.rcc-acis.org/StnMeta'
    headers={
        'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
        'User-Angent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36'
    }
    for c in city_ranges:
        requestData = 'params=%7B%22elems%22%3A%5B%7B%22name%22%3A%22avgt%22%2C%22add%22%3A%22t%22%7D%5D%2C%22sDate%22%3A%222020-01-01%22%2C%22eDate%22%3A%222021-11-20%22%2C%22meta%22%3A%5B%22name%22%2C%22state%22%2C%22ll%22%2C%22sids%22%5D%2C%22bbox%22%3A%5B'\
                    +str(city_ranges[c][0])+'%2C'\
                    +str(city_ranges[c][1])+'%2C'\
                    +str(city_ranges[c][2])+'%2C'\
                    +str(city_ranges[c][3])+'%5D%7D&output=json'
        res = crawl(url, headers, requestData)  
        for station in res['meta']:
            if station['state'] == city_state[c]:
                sids = station['sids']
                for s in sids:
                    id, type = s.split()
                    if type=='1':
                        sid = id+'+'+type
                        #print(sid)
                        cities_stids[c].append(sid)
    with open('cities_stids.json', 'w') as json_file:
        json.dump(cities_stids, json_file)
    return cities_stids

def isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False


def request_avgTemp_each_state(cities_stids):
    url = 'https://data.rcc-acis.org/StnData'
    headers={
        'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
        'User-Angent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36'
    }
    state_code_df = pd.read_csv('state_code.csv', usecols=['State','Code'])
    code_state = {}
    state_n_station = {}
    for _, row in state_code_df.iterrows():
        code_state[row['Code']] = row['State']
    state_temp = collections.defaultdict(list)
    for c in cities_stids:
        #n_stations = len(cities_stids[c])
        for stid in cities_stids[c]:
            print('process:', c, stid)
            requestData = 'params=%7B%22elems%22%3A%5B%7B%22name%22%3A%22avgt%22%2C%22add%22%3A%22t%22%7D%5D%2C%22sid%22%3A%22'\
                    +stid+'%22%2C%22sDate%22%3A%222020-01-01%22%2C%22eDate%22%3A%222021-11-20%22%7D&output=json'
            res = crawl(url, headers, requestData)
            if res['meta']['state'] != 'PR':
                state = code_state[res['meta']['state']]
                if state not in state_n_station:
                    state_n_station[state] = 1
                else:
                    state_n_station[state] += 1
                #n_days = len(res['data']) 
                avgTemp = 30.0
                dates = []
                for i,data in enumerate(res['data']):
                    dates.append(data[0])
                    if isfloat(data[1][0]):
                        avgTemp = float(data[1][0])
                        #print(avgTemp)
                    if len(state_temp[state])>i:
                        state_temp[state][i] += avgTemp
                    else:
                        state_temp[state].append(avgTemp)
            #print(n_days, len(state_temp[state]), state_temp[state])
    # average temp 
    df = pd.DataFrame(data=state_temp)
    df.to_csv('state_temp.csv')
    for s in state_temp:
        state_temp[s] = [a/state_n_station[s] for a in state_temp[s]]
    df = pd.DataFrame(data=state_temp)
    df.to_csv('state_temp.csv')
    df['Date'] = dates
    df = df.set_index('Date')
    df.to_csv('state_temp.csv')

def append_temp_for_SC():
    url = 'https://data.rcc-acis.org/StnData'
    headers={
        'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
        'User-Angent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36'
    }
    requestData = 'params=%7B%22elems%22%3A%5B%7B%22name%22%3A%22avgt%22%2C%22add%22%3A%22t%22%7D%5D%2C%22sid%22%3A%2213782+1%22%2C%22sDate%22%3A%222020-01-01%22%2C%22eDate%22%3A%222021-11-20%22%7D&output=json'
    res = crawl(url, headers, requestData)
    df = pd.read_csv('state_temp_original.csv')
    avgTemp = 30.0
    state_temp = []
    n_days = len(res['data']) 
    for i,data in enumerate(res['data']):
        if isfloat(data[1][0]):
            avgTemp = float(data[1][0])
            #print(avgTemp)
        if len(state_temp)>i:
            state_temp[i] += avgTemp
        else:
            state_temp.append(avgTemp)
    state_temp = [a/n_days for a in state_temp]
    df['South Carolina'] = state_temp
    df.to_csv('state_temp.csv',index = False)

def data_info(file):
    df = pd.read_csv(file)
    print('preview:', df.head())
    print('col length:', len(list(df.columns)))
    print(list(df.columns))
    print('row length:', len(df.index))
    total_states = set(list(state_dict.keys()))
    output_states = set(list(df.columns))
    print('output states length:', len(output_states))
    print('total states length:', len(total_states))
    print('difference:', total_states-output_states)

def main():
    city_state = collect_cities_with_states()
    print(city_state)
    city_ranges = get_cities_lat_lng('uscities_lat_lng.csv', city_state)
    print('get city_ranges, los angeles:', city_ranges['Los Angeles'])
    cities_stids = request_stid_each_city(city_ranges, city_state)
    print('get cities_stid, los angelse:', cities_stids['Los Angeles'])
    request_avgTemp_each_state(cities_stids)





if __name__ == '__main__':
    '''
    url = 'https://data.rcc-acis.org/StnData'
    headers={
        'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
        'User-Angent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36'
    }
    #requestData = 'params=%7B%22elems%22%3A%5B%7B%22name%22%3A%22maxt%22%2C%22add%22%3A%22t%22%7D%2C%7B%22name%22%3A%22mint%22%2C%22add%22%3A%22t%22%7D%2C%7B%22name%22%3A%22avgt%22%2C%22add%22%3A%22t%22%7D%5D%2C%22sid%22%3A%2293134+1%22%2C%22sDate%22%3A%222021-11-01%22%2C%22eDate%22%3A%222021-11-22%22%7D&output=json'
    requestData = 'params=%7B%22elems%22%3A%5B%7B%22name%22%3A%22avgt%22%2C%22add%22%3A%22t%22%7D%5D%2C%22sid%22%3A%22049152+2%22%2C%22sDate%22%3A%222020-01-01%22%2C%22eDate%22%3A%222021-11-20%22%7D&output=json'
    url2 = 'https://data.rcc-acis.org/StnMeta'
    #requestData2 = 'params=%7B%22elems%22%3A%5B%7B%22name%22%3A%22maxt%22%2C%22add%22%3A%22t%22%7D%2C%7B%22name%22%3A%22mint%22%2C%22add%22%3A%22t%22%7D%2C%7B%22name%22%3A%22pcpn%22%2C%22add%22%3A%22t%22%7D%2C%7B%22name%22%3A%22snow%22%2C%22add%22%3A%22t%22%7D%2C%7B%22name%22%3A%22snwd%22%2C%22add%22%3A%22t%22%7D%5D%2C%22sDate%22%3A%222021-11-01%22%2C%22eDate%22%3A%222021-11-22%22%2C%22meta%22%3A%5B%22name%22%2C%22state%22%2C%22ll%22%2C%22sids%22%5D%2C%22bbox%22%3A%5B-74.48400039740095%2C40.3509817883181%2C-73.53045560259905%2C41.0751262116819%5D%7D&output=json'
    #requestData2 = 'params=%7B%22elems%22%3A%5B%7B%22name%22%3A%22maxt%22%2C%22add%22%3A%22t%22%7D%2C%7B%22name%22%3A%22mint%22%2C%22add%22%3A%22t%22%7D%2C%7B%22name%22%3A%22pcpn%22%2C%22add%22%3A%22t%22%7D%2C%7B%22name%22%3A%22snow%22%2C%22add%22%3A%22t%22%7D%2C%7B%22name%22%3A%22snwd%22%2C%22add%22%3A%22t%22%7D%5D%2C%22sDate%22%3A%222021-11-01%22%2C%22eDate%22%3A%222021-11-22%22%2C%22meta%22%3A%5B%22name%22%2C%22state%22%2C%22ll%22%2C%22sids%22%5D%2C%22bbox%22%3A%5B-70.4%2C40.4%2C-73.4%2C41.4%5D%7D&output=json'
    requestData2 = 'params=%7B%22elems%22%3A%5B%7B%22name%22%3A%22avgt%22%2C%22add%22%3A%22t%22%7D%5D%2C%22sDate%22%3A%222020-01-01%22%2C%22eDate%22%3A%222021-11-20%22%2C%22meta%22%3A%5B%22name%22%2C%22state%22%2C%22ll%22%2C%22sids%22%5D%2C%22bbox%22%3A%5B-118.67954077950994%2C33.690165788318104%2C-117.80714722049005%2C34.4143102116819%5D%7D&output=json'
    #crawl(url, headers, requestData)
    crawl(url2, headers, requestData2)
    '''
    
    main()
    #append_temp_for_SC()
    data_info('state_temp.csv')
#https://www3.epa.gov/cgi-bin/broker?_service=data&_server=134.67.99.91&_port=4079&_sessionid=wLJObRu4R52&_PROGRAM=dataprog.ad_viz_plotval_getdata.sas