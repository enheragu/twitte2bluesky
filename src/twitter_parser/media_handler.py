
import os
import re
import requests
from multiprocessing import Pool
from tqdm import tqdm

from utils.log_utils import log_screen
from utils.format_utils import strListRecursive

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

def download_file_multiprocess(args):
    url, save_path = args
    response = requests.get(url, stream=True)

    filename = get_file_name(url)
    if response.status_code == 200:
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024

        with open(os.path.join(save_path,filename), 'wb') as file, tqdm(
            total=total_size, unit='B', unit_scale=True, desc=save_path, leave=False
        ) as progress_bar:
            for chunk in response.iter_content(block_size):
                file.write(chunk)
                progress_bar.update(len(chunk))
    else:
        log_screen(f"Error downloading file {url}: {response.status_code}", level="ERROR")

def download_files_multiprocessing(file_urls, output_path):
    with Pool(processes=6) as pool:
        args = [(url, output_path) for i, url in enumerate(file_urls)]
        list(tqdm(pool.imap(download_file_multiprocess, args), total=len(args)))


def download_tweet_files(tweets_info, output_path = "./"):
    file_urls = []    
    for tweet in tweets_info:
        tweet_media = tweet['media']
        for media_type in ['photos', 'videos']:
            for item in tweet_media[media_type]:
                file_urls.append(item['src'])

    download_files_multiprocessing(file_urls, output_path)
    # log_screen(f"Media is {strListRecursive(file_urls)}")