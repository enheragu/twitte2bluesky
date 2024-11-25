
import os
import re
import copy
import tabulate
import yaml
import argparse

from utils.log_utils import log_screen, loggingShutdown, setLogDefaults, bcolors
from utils.format_utils import replace_emojis, format_date, truncate_string, strListRecursive, strDictRecursive
from twitter_parser.twitter_selenium import twitter_logging, setup_driver ,get_tweet_html, get_cited_tweet_url, get_tweet_screenshot
from twitter_parser.tweet_scrapping import extract_thread_from_html
from twitter_parser.media_handler import download_tweet_files

BASE_URL = 'https://x.com'


def printSummaryTable(tweets_info):
    table_data = copy.deepcopy(tweets_info)
    for index in range(len(table_data)):
        if table_data[index]['user_handle'] is not None:
            formatted_handle = table_data[index]['user_handle'].replace('/', '@')
        formatted_user = f"{table_data[index]['user_name']}\n({formatted_handle})"

        table_data[index].pop('user_handle', None)
        table_data[index].pop('user_name', None)

        table_data[index].pop('id', None)
        table_data[index].pop('parent_id', None)
        table_data[index].pop('child_id', None)

        table_data[index] = {'user': formatted_user, 
                             'date': table_data[index]['date'],
                             'content': table_data[index]['content'],
                             'lang': table_data[index]['lang'],
                             'media': table_data[index]['media'],
                             'cited_tweet': table_data[index]['cited_tweet'],
                             'href': table_data[index]['href']
                             }


    table_format = [["n"] + list(table_data[0].keys())]
    for i, tweet in enumerate(table_data, start=1):
        row_format = [i]
        for data_tag in tweet.keys():
            data = tweet[data_tag]
            data_str = ""
            
            if data is None:
                data_str = ""
            # Clear cited_tweet data, its too much for a table :(
            # elif data_tag == 'cited_tweet' and isinstance(data, dict):
                # data_str = f"Cited tweet from: {data['user_name']}"
            # el
            elif isinstance(data, dict):
                data_str += strDictRecursive(data, max_length=30)
            elif isinstance(data, list):
                data_str += strListRecursive(data, max_length=30)
            elif data_tag == 'date':
                data_str = format_date(data)
            elif data_tag == 'href':
                data_str += truncate_string(str(data), max_length=15, wrap=True)
            else:
                data_str += truncate_string(str(data), max_length=40, wrap=True)
            
            if data_str:
                data_str = replace_emojis(data_str)
            row_format.append(data_str)
        table_format.append(row_format)

    log_screen(f"\n\nFound {len(table_data)} tweets in the thread provided")
    print(tabulate.tabulate(table_format, headers="firstrow", tablefmt="fancy_grid"))

def extend_unique(cited_data, cited_tweet_thread):
    existing_ids = {tweet['id'] for tweet in cited_data}
    for tweet in cited_tweet_thread:
        if tweet['id'] not in existing_ids:
            cited_data.append(tweet)
            existing_ids.add(tweet['id'])
    return cited_data
    
def retrieve_cited_threads(driver, tweets_info, processed_tweets=None, 
                           use_selenium = False, output_path = "./", html_output_path = "./",
                           tweet_author_handle = None):
    # Keep track of processed to avoid repetitions
    if processed_tweets is None:
        processed_tweets = set()

    cited_data = tweets_info
    for tweet in tweets_info:
        if tweet['cited_tweet'] and tweet['href']:
            tweet_id = tweet['cited_tweet']['id']
            
            if tweet_id in processed_tweets:
                log_screen(f"Already processed cited tweet with id: {tweet_id}.")
                continue
            processed_tweets.add(tweet_id)

            child_html_path = os.path.join(html_output_path,f'{tweet_id}_tweet_html.html')
            if use_selenium:
                cited_url = get_cited_tweet_url(driver, f"{BASE_URL}{tweet['href']}")

                if tweet_author_handle and tweet_author_handle not in tweet_id:
                    get_tweet_screenshot(driver, cited_url, os.path.join(output_path, f"{tweet_id}.png"))
                    log_screen(f"Snapshot taken from cited tweet with id: {tweet_id}; {cited_url}.")
                    continue

                tweet['cited_tweet']['href'] = cited_url
                log_screen(f"[PROCESS TWEET] Handling cited url: {cited_url}", text_format=bcolors.OKCYAN)

                cited_html_data = get_tweet_html(driver, cited_url)
                with open(child_html_path, 'w+') as html_file:
                    html_file.write(cited_html_data)
            
            # No selenium case :)
            if tweet_author_handle and tweet_author_handle not in tweet_id:
                continue
            
            log_screen(f"[PROCESS TWEET] Parse HTML data for Tweet {tweet_id} from {child_html_path}", text_format=bcolors.OKCYAN)
            with open(child_html_path, 'r') as html_file:
                cited_html_data = html_file.read()
            
            cited_tweet_thread = extract_thread_from_html(cited_html_data)
            cited_tweet_thread = retrieve_cited_threads(driver=driver, tweets_info=cited_tweet_thread,
                                                        processed_tweets=processed_tweets, use_selenium=use_selenium,
                                                        output_path=output_path, html_output_path=html_output_path,
                                                        tweet_author_handle=tweet_author_handle)
            cited_data = extend_unique(cited_data,cited_tweet_thread)
            
    return cited_data


def tweetScrapping(args):

    setLogDefaults()

    user, password, tweet_url, use_selenium, output_path = args.username, args.password, args.link, args.use_selenium, args.output
    tweet_author_handle = args.author
    
    html_output_path = os.path.join(output_path,"html_data/")
    media_output_path = os.path.join(output_path,"media/")
    yaml_output_path = os.path.join(output_path,"tweet_data.yaml")
    
    if not os.path.exists(html_output_path):
        os.makedirs(html_output_path, exist_ok=True)

    if not os.path.exists(media_output_path):
        os.makedirs(media_output_path, exist_ok=True)
    
    if not is_valid_twitter_url(args.link):
        log_screen("Error: The provided link is not a valid Twitter URL.", level="ERROR")
        exit(1)

    print("Starting scraping...")
    print(f"\t· Username: {args.username}")
    print(f"\t· Tweet URL: {args.link}")
    print(f"\t· Scrapping from: {args.author}")
    print(f"\t· Data will be saved to: {output_path}")
    print(f"\t· Use Selenium: {args.use_selenium}")

                    
    if True or not os.path.exists(yaml_output_path):
        parent_html_path = os.path.join(html_output_path,'parent_html.html')
        if not use_selenium:
            driver = False
        else:
            log_screen(f"[PROCESS TWEET] Handling tweet from: {tweet_url}", text_format=bcolors.OKCYAN)
            driver = setup_driver()
            twitter_logging(driver, args.username, args.password)
            html_data = get_tweet_html(driver, tweet_url)

            with open(parent_html_path, 'w+') as html_file:
                html_file.write(html_data)

        log_screen(f"[PROCESS TWEET] Parse from parent HTML: {parent_html_path}", text_format=bcolors.OKCYAN)
        with open(parent_html_path, 'r') as html_file:
            html_data = html_file.read()

        tweets_info = extract_thread_from_html(html_data)
        tweets_info = retrieve_cited_threads(driver=driver,tweets_info=tweets_info,use_selenium=use_selenium,
                                             output_path=output_path, html_output_path=html_output_path,
                                             tweet_author_handle=tweet_author_handle)

        # Filter tweets in main list from other authors
        filtered_tweets = [tweet for tweet in tweets_info if tweet_author_handle in tweet['id']]

        with open(yaml_output_path, "w+") as yaml_file:
            yaml.dump(filtered_tweets, yaml_file, default_flow_style=False)

        if use_selenium:
            driver.quit()

    with open(yaml_output_path, 'r+') as yaml_file:
        tweets_info = yaml.safe_load(yaml_file)

    download_tweet_files(tweets_info=tweets_info, output_path=media_output_path)

    printSummaryTable(tweets_info)    

    loggingShutdown()

def is_valid_twitter_url(url):
    twitter_regex = re.compile(r'https://(twitter\.com|x\.com)/\w+/status/\d+')
    return twitter_regex.match(url) is not None

def extractTweetArgparse():
    parser = argparse.ArgumentParser(description="Scrape Twitter to extract a web of tweets and threads.")

    parser.add_argument('-u', '--username', type=str, required=True, help="Twitter username to log in.")
    parser.add_argument('-p', '--password', type=str, required=True, help="Twitter password to log in.")
    parser.add_argument('-l', '--link', type=str, required=True, help="URL of the last tweet in the thread to start scraping.")
    parser.add_argument('-o', '--output', type=str, default="./output_data/", help="Path to save the generated results (default: ./output_data/).")
    parser.add_argument('--no_selenium', action='store_false', dest='use_selenium', 
                        help="Disable Selenium and scrape from local HTML files instead.")
    parser.add_argument("--author", default=None,
        help=(
            "Username of the tweet author whose tweets will be scraped. "
            "If not provided, it defaults to the username used for logging in."
        ))
    args = parser.parse_args()
    
    if not args.author:
        args.author = args.username
    
    return args

if __name__ == "__main__":
    
    args = extractTweetArgparse()
    tweetScrapping(args)

