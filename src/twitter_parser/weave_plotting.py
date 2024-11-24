import os
import yaml

yaml_output_path = '/home/quique/eeha/tweet_to_bluesky/output_data/tweet_data.yaml'

with open(yaml_output_path, 'r+') as yaml_file:
    tweets_info = yaml.safe_load(yaml_file)

# Generate the Mermaid code
mermaid_code =  '%%{init: {"flowchart": {"htmlLabels": false}} }%%'
mermaid_code += "flowchart TB\n"

# Iterate through the tweets and create edges
for tweet in tweets_info:
    tweet_format = ":::user_tweet_format"
    if not tweet['user_handle']:
        tweet_content = "None"
    else:
        tweet_content = f"<b>{tweet['user_name']} (<u>{tweet['user_handle'].replace('/','@')}</u>):</b> \n <div style='text-align: left;'>{tweet['content']}</div>"
    parent_id = tweet['parent_id']

    # Add the node for the current tweet
    mermaid_code += f"    {tweet['id']}(\"{tweet_content}\")\n"
    
    if parent_id:
        # Add an edge if there's a parent
        mermaid_code += f"    {parent_id} --> {tweet['id']}{tweet_format}\n"

for tweet in tweets_info:
    tweet_format = ":::user_tweet_format"
    if tweet['cited_tweet'] and tweet['cited_tweet']['id']:
        tag = "Cited"
        if tweet['user_handle'] != tweet['cited_tweet']['user_handle']:
            tweet_format = ":::image_tweet_format"
            tag = "Cited-Img"
        cited_id = tweet['cited_tweet']['id']
        mermaid_code += f"    {tweet['id']} -. {tag} .-> {cited_id}{tweet_format}\n"
        cited_content = f"<b>{tweet['cited_tweet']['user_name']} (<u>{tweet['cited_tweet']['user_handle'].replace('/','@')}</u>):</b> \n <div style='text-align: left;'>{tweet['cited_tweet']['content']}</div>"
        mermaid_code += f"    {cited_id}(\"{cited_content}\")\n"

# Add the custom class definition for the width
# mermaid_code += "\nclassDef wideBox width:600px, font-size:20px, line-height:1.5, max-width:580px;\n"

mermaid_code += "\nclassDef image_tweet_format fill:#EDD734 color:#212227"
mermaid_code += "\nclassDef user_tweet_format fill:#0081A7"
# Save the Mermaid code to a Markdown file
output_file_path = "/home/quique/eeha/tweet_to_bluesky/output_data/tweets_graph.md"
with open(output_file_path, 'w') as md_file:
    md_file.write("```mermaid\n")
    md_file.write(mermaid_code)
    md_file.write("\n```")

print(f"Mermaid code saved to {output_file_path}")
