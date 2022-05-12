from youtube_transcript_api import YouTubeTranscriptApi
from bs4 import BeautifulSoup
import pandas as pd
import requests
import re
import json

df = pd.read_csv('GoogleAds/CA.csv')
df = df[df['ad_type'] == 'Video'].reset_index(drop = True) # only get text ads
df_url = df[['ad_id','ad_url','advertiser_name','impressions','spend_usd']].reset_index(drop = True) 
urls = df_url['ad_url'].to_list() # create a list so we could get the report_urls
# extract youtube urls from reports
youtube_urls = []
youtube_captions = []
for url in urls:
    entity_id = url.split('/')[-3]
    creative_id = url.split('/')[-1]
    report_url = 'https://transparencyreport.google.com/transparencyreport/api/v3/politicalads/creatives/details?entity_id={}&creative_id={}&hl=en'.format(entity_id,creative_id)
    response = requests.get(report_url)
    youtube_id = response.text.split('"')[3]
    youtube_url = 'https://www.youtube.com/watch?v' + youtube_id
    youtube_urls.append(youtube_url)
    # assigning srt variable with the list
    # of dictonaries obtained by the get_transcript() function
    # subs = YouTubeTranscriptApi.get_transcript(youtube_id)
    # #prints the result
    # list = []
    # for sub in subs:
    #   list.append(" " + sub['text'])
    # captions = ""
    # for item in list:
    #   captions += item
    # youtube_captions.append(captions)

youtube_urls.pop(5)
print(youtube_urls)
    

df_youtube = pd.DataFrame(youtube_urls).rename(columns = {0:'youtube_url'})
df = pd.concat([df_url,df_youtube],axis=1)
df['platform'] = 'google'

