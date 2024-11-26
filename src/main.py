
import argparse
from twitter_parser.extract_tweet import extractTweetArgParser, tweetScrapping
from bluesky_publisher.post_bluesky import postBlueskyArgParser



def merge_parsers(parser1, parser2):
    generic_parser = argparse.ArgumentParser(description="Tool to parse tweet threads from a given URL (last tweet url) and post all of that to Bluesky")
    for parser in [parser1, parser2]:
        for action in parser._actions:
            if not any(a.dest == action.dest for a in generic_parser._actions):  # Avoid duplicates
                generic_parser._add_action(action)
    return generic_parser


if __name__ == "__main__":
    
    tw_parser = extractTweetArgParser(add_help = False)
    bs_parser = postBlueskyArgParser(add_help = False)
    
    parser = merge_parsers(tw_parser, bs_parser)
    args = parser.parse_args()

    tweetScrapping(args)