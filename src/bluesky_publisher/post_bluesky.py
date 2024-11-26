
import argparse

def postBlueskyArgParser(add_help = True):
    parser = argparse.ArgumentParser(add_help=add_help, description="BlueskyPublisher based on YAML tweets data.")

    parser.add_argument('-bu', '--bs_username', type=str, required=True, help="Bluesky username to log in.")
    parser.add_argument('-bp', '--bs_password', type=str, required=True, help="Bluesky password to log in.")
    parser.add_argument('-o', '--output', type=str, default="./output_data/", help="Path to get the generated results (default: ./output_data/) to post them to Bluesky.")
    
    return parser
