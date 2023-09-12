
import pandas as pd
import wikipedia
import os
import sys
import redis

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)

# Append the root directory to sys.path
sys.path.append(ROOT_DIR)

from  Redis_Cloud.Redis_Utils import *



def get_wiki_page(title):
    """
    Get the wikipedia page given a title
    """
 
    try:
        return wikipedia.page(title)
    except wikipedia.exceptions.DisambiguationError as e:
        return None #wikipedia.page(e.options[0])
    except wikipedia.exceptions.PageError as e:
        return None
    except Exception as e:
        return None

def recursively_find_all_pages(redis_conn,original_title, titles, titles_so_far=set()):
    #original_title=original_title.replace("'","")
    create_redis_index_for_prefix(redis_conn,original_title.replace("'","").replace(" ","")+"-index",original_title)
        
    if titles==[] :
        titles=[original_title]
    
    all_pages = []
 
    titles = list(set(titles) - titles_so_far)
    for title_so_far in titles_so_far:
         add_to_set_in_redis(redis_conn,"util:wiki_titles",title_so_far)
 
    titles_so_far.update(titles)
    for title in titles:
        print(title)
        page = get_wiki_page(title)
        if page is None :
            continue
        if_already_read_tiles=check_set_item_from_redis(redis_conn,title,"util:wiki_titles")
        if original_title.replace("'","").lower() in page.summary.lower() and not if_already_read_tiles:
            store_text_in_redis_with_vector(redis_conn, page.content, original_title, title)
            add_to_set_in_redis(redis_conn,"util:wiki_titles",title)
            all_pages.append(page)
            #page_links_shrinked=set_difference_with_redis(redis_conn,page.links,"util:wiki_titles")
            new_pages = recursively_find_all_pages(redis_conn,original_title,page.links, titles_so_far)
            
            for pg in new_pages:
                if pg.title not in [p.title for p in all_pages]:
                    all_pages.append(pg)
            titles_so_far.update(page.links)
    return all_pages

r = redis.Redis(host="localhost", port="6379", password="")

pages = recursively_find_all_pages(r,"'Knights Templar'",[])
#print(pages)

for page in pages:
    print(page.title)



