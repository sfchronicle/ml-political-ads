from youtube_transcript_api import YouTubeTranscriptApi
from bs4 import BeautifulSoup
import pandas as pd
import requests
import re
import json
from helper import *

ca_video = get_youtube_id('GoogleAds/CA.csv')
ca_video_clean = check_video(ca_video)
ca_captions = get_captions(ca_video_clean)
ca_captions.to_csv('video_ca.csv')

#print(ca_captions)

tx_video = get_youtube_id('GoogleAds/texas.csv')
tx_video_clean = check_video(tx_video)
tx_captions = get_captions(tx_video_clean)
tx_captions.to_csv('video_tx.csv')
#print(tx_captions)

ny_video = get_youtube_id('GoogleAds/NY.csv')
ny_video_clean = check_video(ny_video)
ny_captions = get_captions(ny_video_clean)
print(ny_captions)