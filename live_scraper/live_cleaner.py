import pandas as pd
import os
import sys

def clean_protothema_text(raw_text):
    if not raw_text or pd.isna(raw_text):
        return None
    
    clean_text = str(raw_text)
    cookie_marker = "Συνεχίζοντας σε αυτό τον ιστότοπο"
    if cookie_marker in clean_text:
        clean_text = clean_text.split(cookie_marker)[0]
        
    menu_marker = "Advertorial"
    if menu_marker in clean_text:
        clean_text = clean_text.split(menu_marker)[-1]
    
    return clean_text.strip()

def general_cleaner(raw_text):
    if not raw_text or pd.isna(raw_text):
        return None
    
    clean_text = str(raw_text)
    
    extra_news_marker = 'Ειδήσεις σήμερα:'
    if extra_news_marker in raw_text:
        clean_text = clean_text.split(extra_news_marker)[0]
        
    extra_news_marker2 = 'Ειδήσεις σήμερα'
    if extra_news_marker2 in raw_text:
        clean_text = clean_text.split(extra_news_marker2)[0]
        
    html_vids = " To view this video please enable JavaScript, and consider upgrading to a web browser that supports HTML5 video"
    if html_vids in raw_text:
        clean_text = clean_text.replace(html_vids, "")
        
    return clean_text.strip()

if not os.path.exists("raw_news.json") or os.path.getsize("raw_news.json") == 0:
    sys.exit(0)

df_raw = pd.read_json("raw_news.json")

if df_raw.empty:
    sys.exit(0)

df_raw.loc[df_raw["source"] == "protothema.gr", 'text'] = df_raw.loc[df_raw["source"] == "protothema.gr", 'text'].apply(clean_protothema_text)
df_raw['text'] = df_raw['text'].apply(general_cleaner)

df = df_raw.dropna(subset=['title', 'date', 'url'])
df = df[df['text'].str.len() > 150]

df['date'] = pd.to_datetime(df['date'], utc=True, errors='coerce')
df = df.dropna(subset=['date'])

if not df.empty:
    df[['source', 'url', 'title', 'date', 'text']].to_json('kafka_feed.jsonl', orient='records', lines=True, force_ascii=False)