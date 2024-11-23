
import argparse
from twitter_parser.extract_tweet import extractTweetArgparse, tweetScrapping

if __name__ == "__main__":
    
    args = extractTweetArgparse()
    tweetScrapping(args)