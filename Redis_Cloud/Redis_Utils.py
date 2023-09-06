
from redis import Redis
from redis.commands.search.query import Query
from redis.commands.search.field import (TextField,VectorField, NumericField)
from redis.commands.search.indexDefinition import ( IndexDefinition,IndexType)
import json
import tiktoken
from typing import Iterator
from numpy import array, average
import openai
import pandas as pd
import os
import sys
# Constant sizes

#VECTOR_DIM = 1536
#TEXT_EMBEDDING_CHUNK_SIZE=300
# Dummy function to generate 1536-dimensional vector
# Replace this with a real embedding function
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))


def get_chunks(text,  tokenizer, TEXT_EMBEDDING_CHUNK_SIZE=300):
    
    tokens = tokenizer.encode(text)
    """Yield successive n-sized chunks from text."""
    i = 0
    while i < len(tokens):
        # Find the nearest end of sentence within a range of 0.5 * n and 1.5 * n tokens
        j = min(i + int(1.5 * TEXT_EMBEDDING_CHUNK_SIZE), len(tokens))
        while j > i + int(0.5 * TEXT_EMBEDDING_CHUNK_SIZE):
            # Decode the tokens and check for full stop or newline
            chunk = tokenizer.decode(tokens[i:j])
            if chunk.endswith(".") or chunk.endswith("\n"):
                break
            j -= 1
        # If no end of sentence found, use n tokens as the chunk size
        if j == i + int(0.5 * TEXT_EMBEDDING_CHUNK_SIZE):
            j = min(i + TEXT_EMBEDDING_CHUNK_SIZE, len(tokens))
        yield tokens[i:j]
        i = j
def get_col_average_from_list_of_lists(list_of_lists):
    """Return the average of each column in a list of lists."""
    if len(list_of_lists) == 1:
        return list_of_lists[0]
    else:
        list_of_lists_array = array(list_of_lists)
        average_embedding = average(list_of_lists_array, axis=0)
        return average_embedding.tolist()


def get_embeddings(text_array, EMBEDDINGS_MODEL = "text-embedding-ada-002"):
    return openai.Engine(id=EMBEDDINGS_MODEL).embeddings(input=text_array)["data"]

def create_embeddings_for_text(text):
    tokenizer = tiktoken.get_encoding("cl100k_base")
    """Return a list of tuples (text_chunk, embedding) and an average embedding for a text."""
    token_chunks = list(get_chunks(text, tokenizer))
    text_chunks = [tokenizer.decode(chunk) for chunk in token_chunks]

    embeddings_response = get_embeddings(text_chunks)
    embeddings = [embedding["embedding"] for embedding in embeddings_response]
    text_embeddings = list(zip(text_chunks, embeddings))

    average_embedding = get_col_average_from_list_of_lists(embeddings)

    return (text_embeddings, average_embedding)

# def generate_custom_vector(chunk_text,tokenizer,TEXT_EMBEDDING_CHUNK_SIZE = 300):
   
#     #"""Return a list of tuples (text_chunk, embedding) and an average embedding for a text."""
#     token_chunks = list(get_chunks(chunk_text, tokenizer, TEXT_EMBEDDING_CHUNK_SIZE))
#     text_chunks = [tokenizer.decode(chunk) for chunk in token_chunks]

#     embeddings_response = get_embeddings(text_chunks, EMBEDDINGS_MODEL = "text-embedding-ada-002")
#     embeddings = [embedding["embedding"] for embedding in embeddings_response]
#     text_embeddings = list(zip(text_chunks, embeddings))

#     average_embedding = get_col_average_from_list_of_lists(embeddings)

#     return (text_embeddings, average_embedding)


# def generate_custom_vector(text):
#     return [0.0] * VECTOR_DIM
def load_vectors(redis_conn, input_list, vector_field_name,PREFIX):
        p = redis_conn.pipeline(transaction=False)
        #r = redis.Redis(host=self.redis_host, port=self.redis_port, password=self.redis_password)
        #p = r.client.pipeline(transaction=False)
        for text in input_list:    
            #hash key
            key=f"{PREFIX}:{text['id']}"
            #hash values
            item_metadata = text['metadata']
            #
            item_keywords_vector = array(text['vector'],dtype= 'float32').tobytes()
            item_metadata[vector_field_name]=item_keywords_vector
            # HSET
            p.hset(key,mapping=item_metadata)
            p.execute()
def get_unique_id_for_file_chunk(filename, chunk_index):
    return str(filename+"-!"+str(chunk_index))

def store_text_in_redis_with_vector(redis_conn,file_body_string,PREFIX,text_embedding_field):
   
    # Clean up the file string by replacing newlines and double spaces and semi-colons
    clean_file_body_string = file_body_string.replace("  ", " ").replace("\n", "; ").replace(';',' ')
    #
    # Add the filename to the text to embed
    text_to_embed = "Field is: {}; {}".format(text_embedding_field, clean_file_body_string)

    # Create embeddings for the text
    try:
        text_embeddings, average_embedding = create_embeddings_for_text(text_to_embed)
        #print("[handle_file_string] Created embedding for {}".format(filename))
    except Exception as e:
        print("[handle_file_string] Error creating embedding: {}".format(e))

    # Get the vectors array of triples: file_chunk_id, embedding, metadata for each embedding
    # Metadata is a dict with keys: filename, file_chunk_index
    vectors = []
    for i, (text_chunk, embedding) in enumerate(text_embeddings):
        id = get_unique_id_for_file_chunk(text_embedding_field, i)
        vectors.append(({'id': id
                         , "vector": embedding, 'metadata': {"filename": text_embedding_field, "text_chunk": text_chunk, "file_chunk_index": i}}))

    try:
        load_vectors(redis_conn,vectors,text_embedding_field,PREFIX)
  
    except Exception as e:
        print(f'Ran into a problem uploading to Redis: {e}')
        
        
def store_list_in_redis(redis_conn, list_key, initial_list):
    for item in initial_list:
        redis_conn.rpush(list_key, item)
    print(f"Initial list stored in Redis under key {list_key}")

def add_to_list_in_redis(redis_conn, list_key, value):
    redis_conn.rpush(list_key, value)

def pull_list_from_redis(redis_conn, list_key):
    redis_list = redis_conn.lrange(list_key, 0, -1)
    return [item.decode("utf-8") for item in redis_list] 

def add_to_set_in_redis(redis_conn, set_key, value):
    redis_conn.sadd(set_key, value)
  
def check_set_item_from_redis(redis_conn, set_item,set_key)->bool:
    exists = redis_conn.sismember(set_key, set_item)
    return exists

def delete_keys_with_prefix(redis_conn,prefix):
    keys_for_the_prefix=redis_conn.scan_iter(prefix+":*")
    for key in keys_for_the_prefix:
        redis_conn.delete(key)

def create_redis_index_for_prefix(redis_conn,index_name,prefix,VECTOR_FIELD_NAME='content_vector',VECTOR_DIM=1536,DISTANCE_METRIC="COSINE"):
    text_embedding = VectorField(VECTOR_FIELD_NAME,"HNSW", {
            "TYPE": "FLOAT32",
            "DIM": VECTOR_DIM,
            "DISTANCE_METRIC": DISTANCE_METRIC
        }
    )
    filename = TextField("filename")
    text_chunk = TextField("text_chunk")
    file_chunk_index = NumericField("file_chunk_index")

    # Add all our field objects to a list to be created as an index
    fields = [filename,text_chunk,file_chunk_index,text_embedding]
    #docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
    #redis_client.ping()

    try:
        redis_conn.ft(index_name).info()
        print("Index already exists")
    except Exception as e:
        print(e)
        # Create RediSearch Index
        print('Not there yet. Creating')
        redis_conn.ft(index_name).create_index(
            fields = fields,
            definition = IndexDefinition(prefix=prefix, index_type=IndexType.HASH))
# r = redis.Redis(host="localhost", port="6379", password="")
# # Initialize parameters
# text_to_embed = "This is a long text that will be divided into chunks of 300 characters. " * 10
# PREFIX = "wiki_page_1"
# text_embedding_field = "Test"

# # Call function
# store_text_in_redis(r,text_to_embed, PREFIX, text_embedding_field)
