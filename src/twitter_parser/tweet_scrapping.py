from bs4 import BeautifulSoup
from datetime import datetime, timezone

from utils.log_utils import log_screen

def extract_media_urls(tweet_div):
    media_urls = {'photos': [], 'videos': [], 'gif': []}
    
    photos_div = tweet_div.find_all('div', {'data-testid': 'tweetPhoto'})
    for photo_div in photos_div:
        try:
            img_tag = photo_div.find('img')
            # Ignore video thumbnails :)
            if img_tag and 'src' in img_tag.attrs:
                if 'video_thumb' not in img_tag['src']:
                    media_urls['photos'].append({'src':img_tag['src'], 'alt':img_tag['alt']})
                else:
                    media_urls['gif'].append({'src':img_tag['src'], 'alt':img_tag['alt']})

            videos = photo_div.find_all('div', {'data-testid': 'videoComponent'})
            for video in videos: 
                try: 
                    video_tag = video.find('video')
                    # Ignore video thumbnails :)
                    if video_tag:
                        if 'poster' in video_tag.attrs: # and 'ext_tw_video_thumb' not in video_tag['src']:
                            media_urls['videos'].append({'src': video_tag['poster'], 'alt':video_tag['alt'] if 'alt' in video_tag else "Video"})
                        
                        source_tag = video_tag.find('source')
                        if source_tag and 'src' in source_tag.attrs: # and 'ext_tw_video_thumb' not in video_tag['src']:    
                            media_urls['videos'].append({'src':source_tag['src'], 'alt':source_tag['alt'] if 'alt' in source_tag else "Video"})
                except Exception as e:
                    log_screen(f"Error al extraer la URL del video for {video_tag}: Exception: {e}", level="ERROR")
        except Exception as e:
            log_screen(f"Error al extraer la URL de la foto for {img_tag}: Exception: {e}", level="ERROR")
    
    return media_urls

def extract_content(content_div):
    if not content_div:
        content="No content available" 
    else:
        content = ''.join([str(element['alt']) if element.name == 'img' else element.get_text() for element in content_div.children])
    return content

def get_tweet_data(tweet_div):
    # print(f"\n\ntweet_div:\n{tweet_div}\n\n")
    tweet_info = {}
    try:
        content_div = tweet_div.find('div', {'data-testid': 'tweetText'})
        content, lang = None, None
        if content_div:
            content = extract_content(content_div)
            lang = '' if 'lang' not in content_div.attrs else content_div['lang']
        
        user_handle, user_name = None, None
        user_div = tweet_div.find('div', {'data-testid': 'User-Name'})
        if user_div:
            user_handle = user_div.find('a', {'role': 'link'})
            user_handle = user_handle['href'] if user_handle else None
            if user_handle is None:
                user_handle_div = user_div.find('div', {'class': 'css-146c3p1 r-dnmrzs r-1udh08x r-3s2u2q r-bcqeeo r-1ttztb7 r-qvutc0 r-37j5jr r-a023e6 r-rjixqe r-16dba41 r-18u37iz r-1wvb978'})
                user_handle = user_handle_div.find('span', {'class': 'css-1jxf684 r-bcqeeo r-1ttztb7 r-qvutc0 r-poiln3'}).get_text()
            user_name = extract_content(user_div.find('div', {'class': 'css-146c3p1 r-bcqeeo r-1ttztb7 r-qvutc0 r-37j5jr r-a023e6 r-rjixqe r-b88u0q r-1awozwy r-6koalj r-1udh08x r-3s2u2q'}))
        
        # Main tweet have different metadata tag ?¿
        metadata_div = tweet_div.find('div', {'class': 'css-175oi2r r-1wbh5a2 r-1a11zyx'})
        if not metadata_div:
            metadata_div = tweet_div.find('div', {'class': 'css-175oi2r r-18u37iz r-1q142lx'})
        date, href = None, None
        if metadata_div:
            data_a = metadata_div.find('a')
            if data_a:
                href = data_a['href'] if 'href' in data_a.attrs else "No href data available"
            date_time = metadata_div.find('time')
            date = date_time['datetime'] if date_time else "No datetime data available"
            
        media_list = extract_media_urls(tweet_div)

        cited_div = tweet_div.find('div', {'role': 'link', 'class': 'css-175oi2r r-adacv r-1udh08x r-1kqtdi0 r-1867qdf r-rs99b7 r-o7ynqc r-6416eg r-1ny4l3l r-1loqt21'}) 
        cited_tweet = None
        if cited_div:
            # print(f"\n\n--------cited_div--------\n{tweet_div}\n--------fin cited_div--------\n")
            cited_tweet = get_tweet_data(cited_div)            
        
        tweet_info = {
            'user_handle': user_handle,
            'user_name': user_name,
            'date': date,
            'lang': lang,
            'content': content,
            'media': media_list,
            'cited_tweet': cited_tweet,
            'href': href
        }
        if all(valor is None for valor in tweet_info.values()):
            log_screen(f"All data is None in dict...", level="ERROR")
            tweet_info = {}

    except Exception as e:
        log_screen(f"Error al extraer información del tweet: {e}", level="ERROR")
        raise e

    return tweet_info



# Función para generar un ID único 
def generate_unique_id(tweet): 
    return f"{tweet['user_handle']}_{tweet['date']}"


"""
    Extracts usable data from Twitter threads
"""
def extract_thread_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    tweets_data = []
    
    tweets = soup.find_all('div', {'class': 'css-175oi2r r-16y2uox r-1wbh5a2 r-1ny4l3l'})
    
    for tweet_div in tweets:
        tweets_data.append(get_tweet_data(tweet_div))

    # Filter duplicated data (based on date and user_handle) and 
    # then order by date :)
    
    def parse_date(date_string):
        if date_string:
            return datetime.fromisoformat(date_string.replace("Z", "+00:00"))  # Convertir 'Z' a '+00:00' para ser compatible con fromisoformat
        return None
    
    seen = set()
    unique_tweets = []
    for tweet in tweets_data:
        tweet_date = parse_date(tweet['date'])
        user_handle = tweet['user_handle']
        # Crear una tupla (date, user_handle) para verificar si ya se ha visto
        if (tweet_date, user_handle) not in seen:
            unique_tweets.append(tweet)
            seen.add((tweet_date, user_handle))
    
    tweets_data_sorted = sorted(unique_tweets, key=lambda x: parse_date(x['date']) if x['date'] is not None else datetime.max.replace(tzinfo=timezone.utc))

    prev_id = None
    for tweet in tweets_data_sorted:
        tweet['id'] = generate_unique_id(tweet)
        tweet['parent_id'] = prev_id
        prev_id = tweet['id']
        if tweet['cited_tweet']:
            tweet['cited_tweet']['id'] = generate_unique_id(tweet['cited_tweet'])

    # Just in case store also child ID to have two-way location
    next_id = None
    for tweet in reversed(tweets_data_sorted):
        tweet['child_id'] = next_id
        next_id = tweet['id']

    return tweets_data_sorted
