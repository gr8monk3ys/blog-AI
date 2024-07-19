import os
import json
import feedparser

def import_rss_feed(url, max_items=5):
    feed = feedparser.parse(url)
    entries = feed.entries[:max_items]
    rss_items = []
    
    for entry in entries:
        item = {
            "title": entry.title,
            "URL": entry.link,
            "description": entry.description,
            "published": entry.published,
            "author": entry.get("author", "N/A"),
            "tags": [tag.term for tag in entry.tags] if "tags" in entry else [],
            "summary": entry.get("summary", "N/A"),
        }
        rss_items.append(item)

    return rss_items

url = 'https://rss.app/feeds/uqWWFSTUYneBNbrq.xml'
res = import_rss_feed(url)

output_dir = 'data/'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

new_dir = os.path.join(output_dir, 'rss.json')
with open(new_dir, 'a') as f:
    json.dump(res, f, indent=2)

