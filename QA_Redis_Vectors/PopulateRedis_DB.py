

# ##
import openai
import os
import requests
import numpy as np
import pandas as pd
from typing import Iterator
import tiktoken
import textract
from numpy import array, average
import sys
import redis  

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
from  Redis_Cloud.Redis_Utils import *
# from redis.commands.search.query import Query
# from redis.commands.search.field import (TextField,VectorField, NumericField)
# from redis.commands.search.indexDefinition import ( IndexDefinition,IndexType)



# # Set our default models and chunking size
# import Redis_Cloud.config #COMPLETIONS_MODEL, EMBEDDINGS_MODEL, CHAT_MODEL, TEXT_EMBEDDING_CHUNK_SIZE, VECTOR_FIELD_NAME
# import warnings 

# from Redis_Cloud.redis_Cloud  import *
# import transformers #import handle_file_string
# from dotenv import load_dotenv

# VECTOR_DIM = 1536 #len(data['title_vector'][0]) # length of the vectors
#VECTOR_NUMBER = len(data)                 # initial number of vectors
# DISTANCE_METRIC = "COSINE" 
# PREFIX = "JackLondon"                            # prefix for the document keys
# INDEX_NAME = "JackLondon-index"  



def PopulateDedisDB(data_dir,prefix,index_name):
    #data_dir = 'C:\\Development\\Data\\JackLondon'

    #transformer=Transformers(PREFIX,INDEX_NAME)
    # ##
    ##time
    #openai.organization = "vladimir.gedgafov"

    # load_dotenv()
    # open_ai_key = os.getenv("OPENAI_API_KEY")
    # openai.api_key = open_ai_key
    redis_conn = redis.Redis(host="localhost", port="6379", password="")
    create_redis_index_for_prefix(redis_conn,index_name,prefix.replace("'","").replace(" ",""))
    #redis_client = get_db()
    #redis_db=Redis_DB(PREFIX,INDEX_NAME)

    # Ignore unclosed SSL socket warnings - optional in case you get these errors

    # warnings.filterwarnings(action="ignore", message="unclosed", category=ImportWarning)
    # warnings.filterwarnings("ignore", category=DeprecationWarning) 
    # pd.set_option('display.max_colwidth', 0)

    csv_files = sorted([x for x in os.listdir(data_dir) if 'DS_Store' not in x])
    #csv_files

 
    # filename = TextField("filename")
    # text_chunk = TextField("text_chunk")
    # file_chunk_index = NumericField("file_chunk_index")

    # # define RediSearch vector fields to use HNSW index

    # text_embedding = VectorField(config.VECTOR_FIELD_NAME,
    #     "HNSW", {
    #         "TYPE": "FLOAT32",
    #         "DIM": config.VECTOR_DIM,
    #         "DISTANCE_METRIC": config.DISTANCE_METRIC
    #     }
    # )
    # Add all our field objects to a list to be created as an index
    # fields = [filename,text_chunk,file_chunk_index,text_embedding]
    #docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
    #redis_client.ping()

    # try:
    #     redis_helper.r.ft(index_name).info()
    #     print("Index already exists")
    # except Exception as e:
    #     print(e)
    #     # Create RediSearch Index
    #     print('Not there yet. Creating')
    #     redis_helper.r.ft(index_name).create_index(
    #         fields = fields,
    #         definition = IndexDefinition(prefix=prefix, index_type=IndexType.HASH)
    #     )


    # Initialise tokenizer
    # tokenizer = tiktoken.get_encoding("cl100k_base")

    # Process each PDF file and prepare for embedding
    for csv_file in csv_files:
        
        csv_path = os.path.join(data_dir,csv_file)
        #print(pdf_path)
        
        # Extract the raw text from each PDF using textract
        # try:
        #     text = textract.process(csv_path, encoding='UTF-8')
        # except Exception as e:
        #     print(e)
        with open(csv_path, 'rb') as file:
            try:
                if_already_read_tiles=check_set_item_from_redis(redis_conn,csv_file,"util:book_titles")
                if not if_already_read_tiles:
                    content = file.read()
                    text = content.decode('utf-8', errors='ignore')
                    store_text_in_redis_with_vector(redis_conn,text,prefix,csv_file)
                    add_to_set_in_redis(redis_conn,"util:book_titles",csv_file)
            except UnicodeDecodeError as e:
                print(f"UnicodeDecodeError: {e}")
 
        
        # Chunk each document, embed the contents and load to Redis
        #handle_file_string((csv_file,text.decode("utf-8")),tokenizer,redis_client,PREFIX)
        #transformers.handle_file_string((csv_file,text.decode("utf-8")),tokenizer,redis_client,config.VECTOR_FIELD_NAME,config.PREFIX)
        #transformers.handle_file_string((csv_file,text),tokenizer,redis_helper.r,config.VECTOR_FIELD_NAME,prefix,redis_helper)


PopulateDedisDB("C:\Development\Data\SherlokHolmes","SherlokHolmes","SherlokHolmes_index")