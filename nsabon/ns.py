import http.client, urllib.request, urllib.parse, urllib.error, base64, ast
import pandas as pd
import math
import numpy as np
import matplotlib.pyplot as plt
import datetime, time
import json
import requests
def getThemPrices(fromP,toP):
    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': 'NS-API',}
    params = urllib.parse.urlencode({
        # Request parameters
        #'date': date,
        'fromStation': fromP,
        'toStation': toP,
    })
    conn = http.client.HTTPSConnection('gateway.apiportal.ns.nl')
    conn.request("GET", "/public-prijsinformatie/prices?%s" % params, "{body}", headers)
    response = conn.getresponse()
    data = response.read()
    dicti=ast.literal_eval(data.decode('utf-8'))
    price = dicti['priceOptions'][1]['totalPrices'][0]['price']/100
    conn.close()
    time.sleep(0.6)
    return price

def applykorting(df, korting_spits, korting_dal, korting_weekend):
    # it calculates the month bill per time (spits:0, dal:1, weekend:2) and korting applied
    return df.loc[df.Spits==0]['Full-Price'].sum()*korting_spits+\
df.loc[df.Spits==1]['Full-Price'].sum()*korting_dal+\
df.loc[df.Spits==2]['Full-Price'].sum()*korting_weekend

weekday=[]           #Day of the week 0 is monday
m=[]                 #month of the trip
y=[]                 #year of the trip
duration =[]         #duration of the trip
spits=[]             #NS time-frame. 0 is spits, 1 is dal-uren, 2 is weekend
price=[]             #how much money the full price costs

#Spits definition
mornspits_start=datetime.time(hour=6,minute=30,second=0)
mornspits_end=datetime.time(hour=9,minute=0,second=0)
avspits_start=datetime.time(hour=16,minute=0,second=0)
avspits_end=datetime.time(hour=18,minute=30,second=0)


data = pd.read_csv("nsdata.csv",sep =',')

#Extraction of data from dataframe and ns API
for index, row in data.iterrows():    
    # In case of taking ov-fiets, the row is full of nans
    if row['Check uit'] is np.nan:
        spits.append(np.nan)
        price.append(np.nan)
        duration.append(np.nan)
    else:        
        # if traveling with the NS check if the trip was done in spits, dal or weekend
        if row['Product'] in ['Treinreizen','Reizen op Saldo NS Korting', 'Reizen op Rekening Trein']:
            wd = datetime.datetime.strptime(data.Datum[2],'%d-%m-%Y').weekday()
            time_trip = pd.to_datetime(row['Check in'],format='%H:%M').time()
            if wd > 4:
                # 2 means weekend
                spits.append(2)
            elif wd == 5 and time_trip>avspits_end:
                # Friday after 6:30 means weekend (2)
                spits.append(2)
            elif avspits_start<=time_trip<avspits_end or mornspits_start<=time_trip<mornspits_end:
                # 0 means weekday morning and afternoon spits
                spits.append(0)
            else:
                # 1 means daluren
                spits.append(1)
            #Check with NS for the full price of a trip
            try:
                if row['Vertrek']==row['Bestemming']:
                    price.append(0)
                elif row['Bestemming'] is np.nan:
                    price.append(np.nan)
                else:
                     price.append(getThemPrices(row['Vertrek'],row['Bestemming']))
            except:
                price.append(np.nan)
        else:
            spits.append(np.nan)
            price.append(np.nan)

print('End of extraction')

# Edition of the dataFrame

data['Spits']=spits
data['Full-Price']=price
checkin=pd.to_datetime(data['Datum']+' '+data['Check in'],format='%d-%m-%Y %H:%M')
checkout=pd.to_datetime(data['Datum']+' '+data['Check uit'],format='%d-%m-%Y %H:%M')
data['Duration']=checkout-checkin
data.loc[data.Duration<pd.to_timedelta(0),'Duration']+=pd.to_timedelta(24*3600*1000000000) 
data=data.set_index(checkin)
del data['Opmerking']
del data['Prive/ Zakelijk']
data.dropna()
del data['Datum']
del data['Bij']
del data['Check in']
del data['Check uit']

# Calculate how much would be payed with each subscription
abon = {'Geen':0,
        'Weekend voordeel': 2,
        'Dal voordeel':3,
        'Spits':19,
        'Weekend vrij':32,
        'Dal vrij':74,
        'Altijd vrij':347
}
geen=[]
w_vdeel=[]
d_vdeel=[]
spits=[]
w_vrij=[]
d_vrij=[]
a_vrij=[]
maand=[]

for year in range(data.index.to_pydatetime().min().year,2020+1):
    for month in range(1,13):
        maand.append(pd.to_datetime(str(year)+'-'+str(month), format='%Y-%m'))
        chunk = data.loc[str(year)+'-'+str(month),['Spits','Full-Price']].dropna()
        geen.append(chunk['Full-Price'].sum()+abon['Geen'])
        w_vdeel.append(applykorting(chunk,1,1,0.6)+abon['Weekend voordeel'])
        d_vdeel.append(applykorting(chunk,1,0.6,1)+abon['Dal voordeel'])
        spits.append(applykorting(chunk,0.8,1,1)+abon['Spits'])
        w_vrij.append(applykorting(chunk,1,1,0)+abon['Weekend vrij'])
        d_vrij.append(applykorting(chunk,1,0,1)+abon['Dal vrij'])
        a_vrij.append(applykorting(chunk,0,0,0)+abon['Altijd vrij'])
        min
dfDic={'month':maand,
    'Geen':geen,
    'Weekend voordeel': w_vdeel,
    'Dal voordeel':d_vdeel,
    'Spits':spits,
    'Weekend vrij':w_vrij,
    'Dal vrij':d_vrij,
    'Altijd vrij':a_vrij}
results=pd.DataFrame.from_dict(dfDic)
results=results.set_index('month')
print(results)

