
from python.api_tools import push_data
from python.userconfig import DEVUSER, DEVPASS, DEVURL, LOCALUSER, LOCALPASS, LOCALURL
import requests
import bs4 as bsoup
import pandas as pd
import time
import datetime
from datetime import datetime
import json

def extract_listings(txt):
    plistings = []
    s = bsoup.BeautifulSoup(txt, 'lxml')
    listings = s.findAll('div', {'class': 'estate-info'})
    for listing in listings:
        price = listing.find('div', {'class': 'estateSummary-price mix-estateSummary_SM-price_sm'}).text
        try:
            title = listing.find('div', {'class': 'estateSummary-title mix-estateSummary_SM-title_sm'}).text
        except:
            pass
        address = listing.find('div', {'class': 'estateSummary-address'}).text
        elems = listing.findAll('div', {'class': 'estateSummary-list'})
        beds = 0
        baths = 0
        sqft = 0
        htype = ''
        lastUpdated = listing.find('em', {'class': 'highlight-text isHiddenSM'})
        if lastUpdated is None:
            lastUpdated = ''
        else:
            lastUpdated = lastUpdated.text.replace('Last updated ', '')
        for elem in elems:
            elems2 = elem.findAll('div')
            for elem2 in elems2:
                txt = elem2.text
                if txt.find('Beds') > 0:
                    beds = float(txt[0:txt.find('Beds')].strip())
                elif txt.find('Baths') > 0:
                    baths = float(txt[0:txt.find('Baths')].strip())
                elif txt.find('Sqft') > 0:
                    sqft = int(txt[0:txt.find('Sqft')].replace(',', '').strip())
                else:
                    htype = txt
        plisting = {'price': price, 'title': title, 'lastUpdated': lastUpdated, 'address': address, 'beds': beds, 'baths': baths, 'sqft': sqft, 'htype': htype}
        plistings.append(plisting)
    return plistings

pnum = 0
morepages = True
plistings = []

print('starting connection')
while morepages:
    pnum += 1
    r = requests.get('http://www.forsalebyowner.com/search/list/80403/house,condo-types/' + str(pnum) + '-page/proximity,desc-sort')
    #r = requests.get('http://www.forsalebyowner.com/search/list/80403/house,condo,townhouse-types/1-page/proximity,desc-sort')
    time.sleep(.5)
    morepages = 'Your search did not yield any results.' not in r.text
    print('At page: {}'.format(pnum))
    if morepages:
        try:
            plistings.extend(extract_listings(r.text))
            print('Got page: {}'.format(pnum))
        except Exception as e:
            raise e
            print('Failed page: {}'.format(pnum))
            continue


df = pd.DataFrame(plistings)

# Create an instance of the data pusher.
# Testing locally here, you need an account to push to:
# http://home-sales-data-api-dev.herokuapp.com    or    http://http://home-sales-data-api.herokuapp.com
print('Get Token')
pusher = push_data(username=LOCALUSER, password=LOCALPASS, baseurl=LOCALURL, geocode='address')
pusher.get_token()
print('API token: {}'.format(pusher.token))


for r in range(df.shape[0]):
    row = df.iloc[r]
    price = row.price.replace('$', '').replace(',', '')
    bedrooms = row.beds
    bathrooms = row.baths
    car_spaces = None
    building_size = row.sqft
    land_size = None
    size_units = 'M' # metric
    raw_address = row.address
    #
    request = {
        "listing_timestamp": str(datetime.now()),
        "listing_type": 'F', # for sale
        "price": price,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "car_spaces": car_spaces,
        "building_size": building_size,
        "land_size": land_size,
        "size_units": size_units,
        "raw_address": raw_address,
        "features": []
        }
    print(request)
    try:
        p = pusher.post_data(data=request)
        time.sleep(0.1)
    except: # did not get a valid raw address, lets not record this.
        # if  "address" in str(e): # "'NoneType' object has no attribute 'address'"
        #     continue
        # else:
        #     print('####')
        #     raise\
        continue



