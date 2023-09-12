
import redis
from redis.commands.search.query import Query
from redis.commands.search.field import (TextField,VectorField, NumericField)
from redis.commands.search.indexDefinition import ( IndexDefinition,IndexType)
import json
import tiktoken
from typing import Iterator
#from numpy import array, average
import numpy
import openai
import pandas as pd
import os
import sys
from datetime import datetime
# Constant sizes

#VECTOR_DIM = 1536
#TEXT_EMBEDDING_CHUNK_SIZE=300

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
        list_of_lists_array = numpy.array(list_of_lists)
        average_embedding = numpy.average(list_of_lists_array, axis=0)
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


def get_unique_id_for_file_chunk(filename, chunk_index):
    return str(filename+"-!"+str(chunk_index))


def load_vectors(redis_conn, input_list, PREFIX,VECTOR_FIELD_NAME='content_vector'):
    p = redis_conn.pipeline(transaction=False)
   
    for text in input_list:    
        #hash key
        key=f"{PREFIX}:{text['id']}"
        #hash values
        item_metadata = text['metadata']
        #
        item_keywords_vector = numpy.array(text['vector'],dtype= 'float32').tobytes()
        item_metadata[VECTOR_FIELD_NAME]=item_keywords_vector
        # HSET
        p.hset(key,mapping=item_metadata)
        p.execute()


def store_text_in_redis_with_vector(redis_conn,file_body_string,PREFIX,text_embedding_field):
   
    # Clean up the file string by replacing newlines and double spaces and semi-colons
    clean_file_body_string = file_body_string.replace("\n", "; ").replace(';',' ').replace("\r", "; ").replace("  ", " ")
    #
    # Add the filename to the text to embed
    text_to_embed = "Field is: {}; {}".format(text_embedding_field, clean_file_body_string)

    # Create embeddings for the text
    try:
        text_embeddings, average_embedding = create_embeddings_for_text(text_to_embed)
        #print("[handle_file_string] Created embedding for {}".format(filename))
    except Exception as e:
        print("[handle_file_string] Error creating embedding: {}".format(e))

    vectors = []
    for i, (text_chunk, embedding) in enumerate(text_embeddings):
        id = get_unique_id_for_file_chunk(text_embedding_field, i)
        vectors.append(({'id': id
                         , "vector": embedding, 'metadata': {"filename": text_embedding_field, "text_chunk": text_chunk, "file_chunk_index": i,
                                                             "lastmodified":datetime.now().strftime("%m/%d/%Y, %H:%M:%S")}}))

    try:
        load_vectors(redis_conn,vectors,PREFIX)
  
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
def set_difference_with_redis(redis_conn, initial_set, set_key):
    redis_set = redis_conn.smembers(set_key)
    redis_set = {x.decode('utf-8') if isinstance(x, bytes) else x for x in redis_set}
    difference_set = set(initial_set) - redis_set
    return difference_set

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
    Lastmodified=TextField("lastmodified")
    # Add all our field objects to a list to be created as an index
    fields = [filename,text_chunk,file_chunk_index,text_embedding,Lastmodified]
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
def LogEvent(redis_conn,request, session, message):
    try:
        #r = self.get_db()
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        ip_address = request.remote_addr
        username = session.get('username', 'Not defined')
        log_entry = f"{current_time} | IP: {ip_address} | Username: {username} | Message: {message}"
        redis_conn.rpush('logs1', log_entry) 
    except Exception as e:
        print(f"Error: {e}")
    
def SignUpUser(redis_conn,username, password):
    # r = self.get_db()
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    user_data = {
        'user_id': str(username),
        'password': str(password),
        'datetime': str(current_time)
    }
    # Convert None values to empty string
    user_data = {k: v if v is not None else "" for k, v in user_data.items()}
    user_data_json = json.dumps(user_data)
    redis_conn.hset('users1', username, user_data_json)

def fetchAllLogs(redis_conn,maxRows):
    #r = self.get_db()
    #all_logs = r.hgetall('logs1')
    items = redis_conn.lrange('logs1', -maxRows, -1)
    items.reverse()
    return items

# Retrieve logs
def fetchAllUsers(redis_conn,maxRows):
    #r = self.get_db()
    all_logs = redis_conn.hgetall('users1')

    return all_logs.items()


def fetchUser(redis_conn,user_id):
    #r = self.get_db()
    user_data = redis_conn.hget('users1', user_id)
    if user_data:
        return eval(user_data)  # Convert string representation back to a dictionary
    return None   
def fetchUser(redis_conn,user_id):
        #r = self.get_db()
        user_data = redis_conn.hget('users1', user_id)
        if user_data:
            return eval(user_data)  # Convert string representation back to a dictionary
        return None   
def LoginUser(redis_conn,username, password):
    user_data=redis_conn.fetchUser(username)
    psw =  user_data['password']
    if(psw==password):
        return username
    else:
        return None

def create_hnsw_index (redis_conn,vector_field_name,vector_dimensions=1536, distance_metric='COSINE'):
    redis_conn.ft().create_index([
        VectorField(vector_field_name, "HNSW", {"TYPE": "FLOAT32", "DIM": vector_dimensions, "DISTANCE_METRIC": distance_metric}),
        TextField("filename"),
        TextField("text_chunk"),        
        NumericField("file_chunk_index"),
        TextField("lastmodified")
    ])

# Create a Redis pipeline to load all the vectors and their metadata


# Make query to Redis
def query_redis(redis_conn,query,index_name,EMBEDDINGS_MODEL = "text-embedding-ada-002", top_k=2,VECTOR_FIELD_NAME='content_vector'):
    ## Creates embedding vector from user query
    embedded_query = numpy.array(openai.Embedding.create(
                                                input=query,
                                                model=EMBEDDINGS_MODEL,
                                            )["data"][0]['embedding'], dtype=numpy.float32).tobytes()

    q = Query(f'*=>[KNN {top_k} @{VECTOR_FIELD_NAME} $vec_param AS vector_score]').sort_by('vector_score').paging(0,top_k).return_fields('vector_score','filename','text_chunk','text_chunk_index').dialect(2) 
    params_dict = {"vec_param": embedded_query}
    #Execute the query
    results = redis_conn.ft(index_name).search(q, query_params = params_dict)
    return results

def get_redis_results(redis_conn,query,index_name):
    
    # Get most relevant documents from Redis
    query_result = query_redis(redis_conn,query,index_name)
    
    # Extract info into a list
    query_result_list = []
    for i, result in enumerate(query_result.docs):
        result_order = i
        text = result.text_chunk
        score = result.vector_score
        query_result_list.append((result_order,text,score))
        
    # Display result as a DataFrame for ease of us
    result_df = pd.DataFrame(query_result_list)
    result_df.columns = ['id','result','certainty']
    return result_df


# redis_conn= redis.Redis(host="localhost", port="6379", password="")
# delete_keys_with_prefix(redis_conn,"'Knights Templar'")
