import re
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from bs4 import FeatureNotFound

from utils.log_utils import log_screen

"""
    It can happen that it includes twitter URL
"""
def get_tweet_url(text):
    if text:
        twitter_regex = re.compile(r'(https://(twitter\.com|x\.com)|)(/\w+/status/\d+)')
        match = twitter_regex.search(text)
        if match:
            return match.group(0)
    return None

"""
    Some tweet view have incomplete ugly URLs, remove them just in case
"""
def filter_incomplete_url(text):
    if text:
        regex = r'\s*(?:x\.com|twitter\.com)/[^\s]+[\u2026]\s*'
        text = re.sub(regex, '', text)
    return text

"""
    Content in tweets should not have twitter urls at all
"""
def filter_tweet_url(text):
    if text:
        regex = r'\s*(https://(twitter\.com|x\.com)|)(/\w+/status/\d+)\s*'
        text = re.sub(regex, '', text)
    return text

"""
    There are two URL formats:
    · https://video.twimg.com/tweet_video/FkU_T4FWQAUMRTy.mp4 → Downloaded as FkU_T4FWQAUMRTy.mp4.
    · https://pbs.twimg.com/media/FkW33SaXEBgIoWR?format=jpg&name=240x240 → Downloaded as FkW33SaXEBgIoWR.jpg.
    This function makes use of regex to extract the name and format from a given URL
"""
def get_file_name(url):
    base_name = url.split("/")[-1].split("?")[0].split(".")[0]
    match = re.search(r'\.(\w+)(\?|$)', url)
    if match:
        return base_name + "." + str(match.group(1))

    match = re.search(r'format=(\w+)&', url)
    if match:
        return base_name + "." + str(match.group(1))

    return base_name + ".unknown"

def extract_media_urls(tweet_div = None):
    media_urls = {'photos': [], 'videos': []} #, 'gif': []} # Videos are finally handled as videos 
    
    if tweet_div:
        photos_div = tweet_div.find_all('div', {'data-testid': 'tweetPhoto'})
        for photo_div in photos_div:
            try:
                img_tag = photo_div.find('img')
                # Ignore video thumbnails :)
                if img_tag and 'src' in img_tag.attrs:
                    if 'video_thumb' not in img_tag['src']:
                        media_urls['photos'].append({'src':img_tag['src'], 'filename': get_file_name(img_tag['src']), 'alt':img_tag['alt']})
                    # else:
                    #     media_urls['videos'].append({'src':img_tag['src'], 'filename': get_file_name(img_tag['src']), 'alt':img_tag['alt']})

                videos = photo_div.find_all('div', {'data-testid': 'videoComponent'})
                for video in videos: 
                    try: 
                        video_tag = video.find('video')
                        # Ignore video thumbnails :)
                        if video_tag:
                            if 'src' in video_tag.attrs: # and 'ext_tw_video_thumb' not in video_tag['src']:
                                media_urls['videos'].append({'src': video_tag['src'], 'filename': get_file_name(video_tag['src']), 'alt':video_tag['aria-label'] if 'aria-label' in video_tag.attrs else "Video"})
                                log_screen(f"Found video :) -> {media_urls['videos'][-1]}")
                            # source_tag = video_tag.find('source')
                            # if source_tag and 'src' in source_tag.attrs: # and 'ext_tw_video_thumb' not in video_tag['src']:    
                            #     media_urls['videos'].append({'src':source_tag['src'], 'alt':source_tag['alt'] if 'alt' in source_tag.attrs     else "Video"})
                    except FeatureNotFound as e:
                        log_screen(f"[Bs4::FeatureNotFound] Error extracitg video URL from {video_tag}: Exception: {e}", level="ERROR")
            except FeatureNotFound as e:
                log_screen(f"[Bs4::FeatureNotFound] Error extracitg image URL from {img_tag}: Exception: {e}", level="ERROR")
        
    return media_urls

def extract_content(content_div):
    if not content_div:
        content="No content available" 
    else:
        content = ''.join([
            str(element['alt']) if element.name == 'img' else  # Imag, usually emojy takes alt
            element.get('href', '') if element.name == 'a' else  # a could imply having a link in there (cite tweet maybe)
            element.get_text()
            for element in content_div.children
        ])

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
        
        media_div = tweet_div.find('div', {'class': 'css-175oi2r r-1kqtdi0 r-1phboty r-rs99b7 r-1867qdf r-1udh08x r-o7ynqc r-6416eg r-1ny4l3l'})
        if not media_div: # Cited tweets have media in another place :)
            media_div = tweet_div.find('div', {'data-testid': 'testCondensedMedia'})
        media_list = extract_media_urls(media_div)

        cited_div = tweet_div.find('div', {'role': 'link', 'class': 'css-175oi2r r-adacv r-1udh08x r-1kqtdi0 r-1867qdf r-rs99b7 r-o7ynqc r-6416eg r-1ny4l3l r-1loqt21'}) 
        cited_tweet = None
        if cited_div:
            # print(f"\n\n--------cited_div--------\n{tweet_div}\n--------fin cited_div--------\n")
            cited_tweet = get_tweet_data(cited_div)

        # If tweet was deleted or account blocked it just displays URL...
        cited_url = get_tweet_url(content)
        if cited_url:
            log_screen(f"Detected cite from missing tweet from {cited_url}", level="WARNING")
            cited_tweet = {
                'user_handle': f"/{cited_url.split('/')[-3]}",
                'user_name': cited_url.split('/')[-3],
                'date': None,
                'lang': None,
                'content': f"[!] Tweet removed or account blocked/removed: {cited_url}",
                'media': extract_media_urls(),
                'cited_tweet': None,
                'href': cited_url
            }

        # Remove tweet urls from content as it should have none
        content = filter_tweet_url(content)
        content = filter_incomplete_url(content)
        tweet_info = {
            'user_handle': user_handle.replace("@","/") if user_handle else None,
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
    except FeatureNotFound as e:
        log_screen(f"[Bs4::FeatureNotFound] Error extracting tweet information {e}", level="ERROR")
    except Exception as e:
        log_screen(f"Error extracting tweet information: {e}", level="ERROR")
        raise e

    return tweet_info



# Función para generar un ID único 
def generate_unique_id(tweet): 
    return f"{tweet['user_handle']}_{tweet['date']}".replace("/","")


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
