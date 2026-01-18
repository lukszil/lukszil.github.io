import requests
import json
import os
import xml.etree.ElementTree as ET
import random
import string
from textblob import TextBlob  # <--- EZ AZ ÚJ VARÁZSLAT

def analyze_smart_sentiment(text):
    """
    Kombinált elemzés:
    1. Kulcsszavak alapján meghatározzuk a TÉMÁT (Category).
    2. TextBlob segítségével kiszámoljuk a valódi HANGULATOT (Score).
    """
    
    # --- 1. NLP Elemzés (A "Matek") ---
    blob = TextBlob(text)
    # A polarity egy szám -1.0 és 1.0 között. 
    # Megszorozzuk 10-zel, hogy a grafikonunk skálájára (-10-től +10-ig) illeszkedjen.
    raw_score = blob.sentiment.polarity * 10
    
    # --- 2. Téma Kategorizálás (A "Címke") ---
    text_lower = text.lower()
    translator = str.maketrans('', '', string.punctuation)
    clean_words = set(text_lower.translate(translator).split())
    
    category = "Egyéb Hír"
    
    # Ha a TextBlob semlegesnek (0) érzi, de mi tudjuk, hogy ezek a kulcsszavak fontosak,
    # akkor manuálisan "meglökjük" a pontszámot a megfelelő irányba.
    
    # Negatív témák
    if any(w in clean_words for w in ['lawsuit', 'sue', 'sued', 'legal', 'guilty', 'infringement']):
        category = "Per & Jog"
        if raw_score > -2: raw_score -= 5 # Ha a gép nem érti, hogy a per rossz, segítünk neki
        
    elif any(w in clean_words for w in ['layoff', 'layoffs', 'fire', 'fired', 'cut', 'cuts', 'job', 'crisis', 'shut']):
        category = "Válság/Leépítés"
        if raw_score > -2: raw_score -= 6
        
    elif any(w in clean_words for w in ['ai', 'fake', 'deepfake', 'fraud', 'scam', 'threat']):
        category = "AI Veszély"
        if raw_score > -2: raw_score -= 7

    # Pozitív témák
    elif any(w in clean_words for w in ['billion', 'million', 'revenue', 'profit', 'earnings', 'quarterly', 'growth']):
        category = "Pénzügy"
        if raw_score < 2: raw_score += 4
        
    elif any(w in clean_words for w in ['record', 'hit', 'top', 'success', 'boom', 'historic', 'milestone']):
        category = "Növekedés"
        if raw_score < 2: raw_score += 3
        
    elif any(w in clean_words for w in ['deal', 'signed', 'partnership', 'acquisition', 'bought', 'launch', 'new']):
        category = "Üzletkötés"
        if raw_score < 1: raw_score += 2

    # Végső korrekció: A pontszám maradjon -10 és 10 között
    final_score = max(min(raw_score, 10), -10)
    
    # Ha pontosan 0 lett (semleges), adjunk neki pici zajt, hogy ne takarják egymást
    if final_score == 0:
        final_score = random.uniform(-1.5, 1.5)

    return category, final_score

def scrape_rss_feed():
    url = "https://www.musicbusinessworldwide.com/feed/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        print(f"📡 Kapcsolódás: {url}...")
        response = requests.get(url, headers=headers)
        root = ET.fromstring(response.content)
        
        items = root.findall('./channel/item')
        print(f"✅ Letöltve: {len(items)} hír. Elemzés indítása...")
        
        raw_data = []

        # Az első 50 hír feldolgozása
        for item in items[:50]:
            title = item.find('title').text
            link = item.find('link').text
            
            # ITT TÖRTÉNIK A VARÁZSLAT
            category, sentiment = analyze_smart_sentiment(title)
            
            # Rövid címke a tooltiphez
            short_label = title[:50] + "..." if len(title) > 50 else title
            
            raw_data.append({
                "label": short_label,
                "full_title": title,
                "category": category,
                "sentiment": round(sentiment, 2), # Kerekítés 2 tizedesre
                "url": link,
                "jitter": random.random()
            })

        # Mentés
        if not os.path.exists('data'): os.makedirs('data')
        
        output_path = 'data/scraped_trends.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, ensure_ascii=False, indent=4)
            
        print(f"🚀 KÉSZ! {len(raw_data)} elemzett hír elmentve ide: {output_path}")
        print("-" * 30)
        print(f"Példa elemzés:\nCím: {raw_data[0]['full_title']}\nKategória: {raw_data[0]['category']}\nPontszám: {raw_data[0]['sentiment']}")
        
    except Exception as e:
        print(f"❌ Hiba: {e}")

if __name__ == "__main__":
    scrape_rss_feed()