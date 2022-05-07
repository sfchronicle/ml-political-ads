{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 7,
   "id": "88acc7d5",
   "metadata": {},
   "outputs": [],
   "source": [
    "from bs4 import BeautifulSoup\n",
    "import pandas as pd\n",
    "import requests\n",
    "import re\n",
    "import json\n",
    "import spacy\n",
    "from spacy.matcher import PhraseMatcher"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 8,
   "id": "4c72fcd3",
   "metadata": {},
   "outputs": [],
   "source": [
    "def get_text_from_csv(fn): # get ad's text from csv file, return a dataframe with text, ad_id,ad_url, and report_url\n",
    "    df = pd.read_csv(fn)\n",
    "    df = df[df['ad_type'] == 'Text'].reset_index(drop = True) # only get text ads\n",
    "    df_url = df[['ad_id','ad_url']].reset_index(drop = True) # get the urls\n",
    "    urls = df_url['ad_url'].to_list() # create a list so we could get the report_urls\n",
    "    report_urls = []\n",
    "    for url in urls:\n",
    "        entity_id = url.split('/')[-3]\n",
    "        creative_id = url.split('/')[-1]\n",
    "        report_url = 'https://transparencyreport.google.com/transparencyreport/api/v3/politicalads/creatives/details?entity_id={}&creative_id={}&hl=en'.format(entity_id,creative_id)\n",
    "        report_urls.append(report_url)\n",
    "    df_report = pd.DataFrame(report_urls).rename(columns = {0:'report_url'})\n",
    "    ad_text = [] # get texts from reports\n",
    "    for report_url in report_urls:\n",
    "        response = requests.get(report_url)\n",
    "        text = response.text.split('\"]')[0].split('[')[-1]\n",
    "        ad_text.append(text)  \n",
    "    df_text = pd.DataFrame(ad_text).rename(columns = {0:'text'})\n",
    "    df_new = df[df['ad_type']=='Text'][['ad_id','ad_url']].reset_index(drop = True) \n",
    "    df = pd.concat([df_new,df_report,df_text],axis=1)\n",
    "    return df  "
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 9,
   "id": "5b928802",
   "metadata": {},
   "outputs": [],
   "source": [
    "# check the dataset \n",
    "def check_null(df_text):\n",
    "    if df_text['text'].isnull().sum():\n",
    "        print (df_text['text'].isnull().sum())\n",
    "        df_text = df_text[df_text['text'].notnull()]\n",
    "        df_text.reset_index(drop=True,inplace=True)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 10,
   "id": "0daaeae0",
   "metadata": {},
   "outputs": [],
   "source": [
    "# function that filter the urls and symbols in the text \n",
    "def clean_text(df_text):\n",
    "    def filter_text(x):\n",
    "        url = 'http[s]?://\\S+'\n",
    "        x = re.sub(url,'',x)\n",
    "        x = re.sub(\"[^\\w\\s]\",' ',x) # filter symbols\n",
    "        x = re.sub(\"\\s+\",' ',x)\n",
    "        ls=[w.lower() for w in x.split()] \n",
    "        return ' '.join(ls)\n",
    "    df_text['text'] = df_text['text'].astype(str).apply(lambda x: filter_text(x))\n",
    "    df_text['text'] = df_text['text'].replace('/u0026', ' ')\n",
    "    df_text.drop_duplicates(subset = 'text',keep = 'first', inplace = True)\n",
    "    df_text.reset_index(drop = True,inplace = True)\n",
    "    return df_text"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 11,
   "id": "a3c8ef8c",
   "metadata": {},
   "outputs": [],
   "source": [
    "# the function that find the lexicon words in the text\n",
    "def find_words(x,lexicon):\n",
    "    topics= lexicon.keys()  \n",
    "    nlp = spacy.load(\"/usr/local/Cellar/jupyterlab/3.2.9/libexec/lib/python3.9/site-packages/en_core_web_lg/en_core_web_lg-3.2.0/\")\n",
    "    doc = nlp(x) # nlp() is spaCy 2.2 English language model \n",
    "    words= []\n",
    "    for t in topics:\n",
    "        matcher = PhraseMatcher(nlp.vocab)\n",
    "        terms= lexicon[t]\n",
    "        patterns = [nlp.make_doc(text) for text in terms]\n",
    "        matcher.add(\"TerminologyList\", patterns) # spaCy2.2 phrase matcher\n",
    "        matches = matcher(doc)\n",
    "        for match_id, start,end in matches:\n",
    "            span = doc[start:end]\n",
    "            words.append(span.text)\n",
    "    if words:\n",
    "        words = list(set(words))\n",
    "        return ','.join(words)\n",
    "    else:\n",
    "        return('no words')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 12,
   "id": "ff10e181",
   "metadata": {},
   "outputs": [],
   "source": [
    "# tagging the topic in each message\n",
    "def find_topic(x,lexicon):\n",
    "    topics= lexicon.keys()    \n",
    "    if x=='no words':\n",
    "        return ''    \n",
    "    if x != 'no words': \n",
    "        words = x.split(',')\n",
    "        labels = []        \n",
    "        for t in topics:            \n",
    "            terms = lexicon[t]\n",
    "            if set(words)&set(terms):\n",
    "                labels.append(t)                \n",
    "                #l = sorted(labels)        \n",
    "        return  ','.join(sorted(labels))\n",
    "                \n",
    "        #return ','.join(labels)\n",
    "            "
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 18,
   "id": "dc891547",
   "metadata": {},
   "outputs": [],
   "source": [
    "def get_word_lable(df_text,lexicon):\n",
    "    with open (lexicon) as f:\n",
    "        dic = json.load(f)\n",
    "    nlp = spacy.load(\"/usr/local/Cellar/jupyterlab/3.2.9/libexec/lib/python3.9/site-packages/en_core_web_lg/en_core_web_lg-3.2.0/\")\n",
    "    df_text['words'] = df_text['text'].astype(str).apply(lambda x: find_words(x,dic))\n",
    "    df_text['m_label'] = df_text['words'].apply(lambda x: find_topic(x,dic))\n",
    "    df_text['m_label'] = df_text['m_label'].apply(lambda x: 'no topic' if x=='' else x)\n",
    "    return df_text"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 19,
   "id": "7f5e156b",
   "metadata": {},
   "outputs": [],
   "source": [
    "def count_topic(df_text):\n",
    "    df_tag = df_text['m_label'].value_counts().rename_axis('topics').reset_index(name='counts')\n",
    "    df_tag = df_tag.assign(single_topic=df_tag['topics'].str.split(',')).explode('single_topic').reset_index(drop = True)\n",
    "    df_tag = df_tag.groupby('single_topic').sum().reset_index().sort_values(by = 'counts', ascending = False)\n",
    "    df_tag.reset_index(drop = True, inplace = True)\n",
    "    return df_tag"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 15,
   "id": "9be8a97d",
   "metadata": {},
   "outputs": [],
   "source": [
    "def count_word(df_text):\n",
    "    df_words = df_text['words'].value_counts().rename_axis('words').reset_index(name='counts')\n",
    "    df_words = df_words.assign(single_word=df_words['words'].str.split(',')).explode('single_word').reset_index(drop = True)\n",
    "    df_words = df_words.groupby('single_word').sum().reset_index().sort_values(by = 'counts', ascending = False)\n",
    "    df_words.reset_index(drop = True, inplace = True)\n",
    "    return df_words"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "be9a9f65",
   "metadata": {},
   "outputs": [],
   "source": []
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3 (ipykernel)",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.9.10"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
