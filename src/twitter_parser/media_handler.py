
import os
import re
import requests
from multiprocessing import Pool
from tqdm import tqdm

from utils.log_utils import log_screen
from utils.format_utils import strListRecursive


def download_file_multiprocess(args):
    (url, filename), save_path = args
    response = requests.get(url, stream=True)

    if os.path.exists(os.path.join(save_path,filename)):
        return
    
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

def download_files_multiprocessing(files_data, output_path):
    with Pool(processes=6) as pool:
        args = [(file_data, output_path) for i, file_data in enumerate(files_data)]
        list(tqdm(pool.imap(download_file_multiprocess, args), total=len(args)))


def download_tweet_files(tweets_info, output_path = "./"):
    files_data = []    
    for tweet in tweets_info:
        tweet_media = tweet['media']
        for media_type in ['photos', 'videos']:
            for item in tweet_media[media_type]:
                files_data.append((item['src'], item['filename']))

    download_files_multiprocessing(files_data, output_path)