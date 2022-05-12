from bs4 import BeautifulSoup
import pandas as pd
import requests
import re
import json
import spacy
from spacy.matcher import PhraseMatcher
import numpy as np
from youtube_transcript_api import YouTubeTranscriptApi

def get_text_from_csv(fn): # get ad's text from csv file, return a dataframe with text, ad_id,ad_url, and report_url
    df = pd.read_csv(fn)
    df = df[df['ad_type'] == 'Text'].reset_index(drop = True) # only get text ads
    df_url = df[['ad_id','ad_url']].reset_index(drop = True) # get the urls
    urls = df_url['ad_url'].to_list() # create a list so we could get the report_urls
    report_urls = []
    for url in urls:
        entity_id = url.split('/')[-3]
        creative_id = url.split('/')[-1]
        report_url = 'https://transparencyreport.google.com/transparencyreport/api/v3/politicalads/creatives/details?entity_id={}&creative_id={}&hl=en'.format(entity_id,creative_id)
        report_urls.append(report_url)
    ad_text = [] # get texts from reports
    for report_url in report_urls:
        response = requests.get(report_url)
        text = response.text.split('"]')[0].split('[')[-1]
        ad_text.append(text)  
    df_text = pd.DataFrame(ad_text).rename(columns = {0:'text'})
    df_new = df[df['ad_type']=='Text'][['advertiser_name']].reset_index(drop = True) 
    df = pd.concat([df_text,df_new],axis=1)
    df['platform'] = 'google'
    return df  

# check the dataset 
def check_null(df_text):
    if df_text['text'].isnull().sum():
        print (df_text['text'].isnull().sum())
        df_text = df_text[df_text['text'].notnull()]
        df_text.reset_index(drop=True,inplace=True)
        return df_text


# function that filter the urls and symbols in the text 
def clean_text(df_text):
    def filter_text(x):
        url = 'http[s]?://\S+'
        x = re.sub(url,'',x)
        x = re.sub("[^\w\s]",' ',x) # filter symbols
        x = re.sub("\s+",' ',x)
        ls=[w.lower() for w in x.split()] 
        return ' '.join(ls)
    df_text['text'] = df_text['text'].astype(str).apply(lambda x: filter_text(x))
    df_text['text'] = df_text['text'].replace('/u0026', ' ')
    df_text.drop_duplicates(subset = 'text',keep = 'first', inplace = True)
    df_text.reset_index(drop = True,inplace = True)
    return df_text

# the function that find the lexicon words in the text
def find_words(x,lexicon):   
    topics= lexicon.keys()  
    nlp = spacy.load("/usr/local/Cellar/jupyterlab/3.2.9/libexec/lib/python3.9/site-packages/en_core_web_lg/en_core_web_lg-3.2.0/")
    doc = nlp(x) # nlp() is spaCy 2.2 English language model 
    words= []
    for t in topics:
        matcher = PhraseMatcher(nlp.vocab)
        terms= lexicon[t]
        patterns = [nlp.make_doc(text) for text in terms]
        matcher.add("TerminologyList", patterns) # spaCy2.2 phrase matcher
        matches = matcher(doc)
        for match_id, start,end in matches:
            span = doc[start:end]
            words.append(span.text)
    if words:
        words = list(set(words))
        return ','.join(words)
    else:
        return('no words')

# tagging the topic in each message
def find_topic(x,lexicon):
    topics= lexicon.keys()    
    if x=='no words':
        return ''    
    if x != 'no words': 
        words = x.split(',')
        labels = []        
        for t in topics:            
            terms = lexicon[t]
            if set(words)&set(terms):
                labels.append(t)                
                #l = sorted(labels)        
        return  ','.join(sorted(labels))
                
        #return ','.join(labels)

def get_word_lable(df_text,lexicon):
    with open (lexicon) as f:
        dic = json.load(f)
    df_text['words'] = df_text['text'].astype(str).apply(lambda x: find_words(x,dic))
    df_text['m_label'] = df_text['words'].apply(lambda x: find_topic(x,dic))
    df_text['m_label'] = df_text['m_label'].apply(lambda x: 'no topic' if x=='' else x)
    return df_text

def count_topic(df_text):
    df_tag = df_text['m_label'].value_counts().rename_axis('topics').reset_index(name='counts')
    df_tag = df_tag.assign(single_topic=df_tag['topics'].str.split(',')).explode('single_topic').reset_index(drop = True)
    df_tag = df_tag.groupby('single_topic').sum().reset_index().sort_values(by = 'counts', ascending = False)
    df_tag.reset_index(drop = True, inplace = True)
    return df_tag

def count_word(df_text):
    df_words = df_text['words'].value_counts().rename_axis('words').reset_index(name='counts')
    df_words = df_words.assign(single_word=df_words['words'].str.split(',')).explode('single_word').reset_index(drop = True)
    df_words = df_words.groupby('single_word').sum().reset_index().sort_values(by = 'counts', ascending = False)
    df_words.reset_index(drop = True, inplace = True)
    return df_words
          
def read_fb(fn):
    facebook_df = pd.read_csv(fn)
    facebook_df.drop(columns = ['Unnamed: 0'],inplace = True)
    facebook_df.rename(columns = {'byline':'advertiser_name'},inplace = True)
    facebook_df['platform'] = 'facebook'
    pd.set_option('display.max_colwidth', None)
    return facebook_df

# go through the csv file, get youtube video's ids from all video ads. Add new column 'youtube_id' 
# before running this function, make sure the csv file includes ad_url
def get_youtube_id(fn): 
    df = pd.read_csv(fn)
    df = df[df['ad_type'] == 'Video'].reset_index(drop = True) # only get video ads
    df_video = df[['ad_url','advertiser_name','impressions','spend_usd']].reset_index(drop = True) 
    urls = df_video['ad_url'].to_list() # 
    youtube_ids = [] # get youtube id
    for url in urls:
        entity_id = url.split('/')[-3]
        creative_id = url.split('/')[-1]
        report_url = 'https://transparencyreport.google.com/transparencyreport/api/v3/politicalads/creatives/details?entity_id={}&creative_id={}&hl=en'.format(entity_id,creative_id)
        response = requests.get(report_url)
        try:
            youtube_id = response.text.split('"')[3]
            if len(list(youtube_id)) > 11: # mark ads violating google polices
                youtube_id = 'youtube_id not available: this ad violated google ad policies.' 
            #print(youtube_id + ', ' + creative_id)
        except IndexError: # mark ads cannot be loaded
            youtube_id = 'youtube_id not available: cannot load the video with this ad_url.'
            #print("can't load this video, " + report_url)
            pass
        youtube_ids.append(youtube_id)
    df_video['youtube_id'] = youtube_ids
    return df_video

# check all videos, see which are available and drop duplicates. Add a new column video_available
def check_video(df_video): 
  for id in df_video['youtube_id']:
    if len(list(id)) == 11:
      df_video.drop_duplicates(subset = 'youtube_id',keep = 'first', inplace = True)
      df_video.reset_index(drop = True, inplace=True)
      yes_video = df_video['youtube_id'].str.len() == 11
      df_video['video_available'] = yes_video
      return df_video

# use youtube_id to get captions. Add a new column youtube_captions
def get_captions(df_video):
  youtube_captions = []
  for youtube_id in df_video['youtube_id']:
    try:
      subs = YouTubeTranscriptApi.get_transcript(youtube_id)
      #prints the result
      alist = []
      for sub in subs:
        alist.append(" " + sub['text'])
      captions = ""
      for item in alist:
        captions += item
    except Exception as e:
      captions = e   
    youtube_captions.append(captions)
    df_video['text'] = youtube_captions
    return df_video