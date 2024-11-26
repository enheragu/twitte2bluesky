

if __name__ == "__main__":
    import os
    import sys

    # Ensure paths are included so that all paths in this repo are found
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for path_include in ["", "..", "../.."]:
        complete_path = os.path.join(script_dir,path_include)
        if complete_path not in sys.path:
            sys.path.insert(0, complete_path)

    from twitter_parser.extract_tweet import extractTweetArgParser, tweetScrapping

    parser = extractTweetArgParser()
    args = parser.parse_args()   
    tweetScrapping(args)