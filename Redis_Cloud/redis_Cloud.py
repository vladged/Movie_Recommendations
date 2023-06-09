import redis
from dotenv import load_dotenv
import os
import datetime
import json
from redis.commands.search.field import VectorField
from redis.commands.search.field import TextField, NumericField
from redis.commands.search.query import Query
import openai
import pandas as pd 
import numpy as np
from . import config 
import sys

# SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# sys.path.append(os.path.dirname(SCRIPT_DIR))

# Create a Redis client
class Redis_helper:
    def __init__(self,redis_host,redis_port,redis_password_name=""):
    
        self.redis_host = redis_host
        self.redis_port = redis_port
        load_dotenv()
        # redis_password = os.getenv("redis_cloud_password")
        if redis_password_name!="":
            self.redis_password = os.getenv(redis_password_name)
        else:
             self.redis_password =""
        
        
        self.r=self.get_db()
    # redis_host = 'redis-13531.c56.east-us.azure.cloud.redislabs.com'
    # redis_port = '13531'

 

    def get_db(self):
        if self.redis_password!="":
            r = redis.Redis(host=self.redis_host, port=self.redis_port, password=self.redis_password)
        else:
           r = redis.Redis(host=self.redis_host, port=self.redis_port, db=0,decode_responses=False)  
        return r
        # r = Redis(host=host, port=port, db=db,decode_responses=False)
        # return r
    # Store logs
    # def LogEvent(request,session,message,error_message=""):
    #     user_ip = request.remote_addr
    #     user_name = session.get('username')
    #     if(user_name==None):
    #         user_name="Not defined"
    #     r = get_db()
    #     #log_id = r.incr('log_id_counter')
    #     current_time = datetime.datetime.now().isoformat()

    #     log_item = {
    #        #'id':log_id,
    #         'username': user_name,
    #         'ip': user_ip,
    #         'time': current_time,
    #         'message': message,
    #         'errorMessage': error_message
    #     }
    #     log_json = json.dumps(log_item)
    #     # Store log item in Redis
    #     r.rpush('logs', log_json)
        
    def LogEvent(self,request, session, message):
        try:
            #r = self.get_db()
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
            ip_address = request.remote_addr
            username = session.get('username', 'Not defined')
            log_entry = f"{current_time} | IP: {ip_address} | Username: {username} | Message: {message}"
            self.r.rpush('logs1', log_entry) 
        except Exception as e:
            print(f"Error: {e}")
        
    def SignUpUser(self,username, password):
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
        self.r.hset('users1', username, user_data_json)
    
    def fetchAllLogs(self,maxRows):
        #r = self.get_db()
        #all_logs = r.hgetall('logs1')
        items = self.r.lrange('logs1', -maxRows, -1)
        items.reverse()
        return items

    # Retrieve logs
    def fetchAllUsers(self,maxRows):
        #r = self.get_db()
        all_logs = self.r.hgetall('users1')
    
        return all_logs.items()

    # Print retrieved logs
    # for log_id, log_message in all_logs.items():
    #     print(f"Log ID: {log_id.decode('utf-8')}, Message: {log_message.decode('utf-8')}")
    ##############################################################################################   
    
    # def fetchUser(username):
    #     r = get_db()
    #     user =  r.hget('users1',username)
    #     return user
    def fetchUser(self,user_id):
        #r = self.get_db()
        user_data = self.r.hget('users1', user_id)
        if user_data:
            return eval(user_data)  # Convert string representation back to a dictionary
        return None   
    def LoginUser(self,username, password):
        user_data=self.fetchUser(username)
        psw =  user_data['password']
        if(psw==password):
            return username
        else:
            return None
        
    # def get_redis_connection(host='localhost',port='6379',db=0):
    #     r = Redis(host=host, port=port, db=db,decode_responses=False)
    #     return r

    # Create a Redis index to hold our data


    def create_hnsw_index (self,vector_field_name,vector_dimensions=1536, distance_metric='COSINE'):
        self.r.ft().create_index([
            VectorField(vector_field_name, "HNSW", {"TYPE": "FLOAT32", "DIM": vector_dimensions, "DISTANCE_METRIC": distance_metric}),
            TextField("filename"),
            TextField("text_chunk"),        
            NumericField("file_chunk_index")
        ])

    # Create a Redis pipeline to load all the vectors and their metadata
   
    def load_vectors(self, input_list, vector_field_name,PREFIX):
        p = self.r.pipeline(transaction=False)
        #r = redis.Redis(host=self.redis_host, port=self.redis_port, password=self.redis_password)
        #p = r.client.pipeline(transaction=False)
        for text in input_list:    
            #hash key
            key=f"{PREFIX}:{text['id']}"
            #hash values
            item_metadata = text['metadata']
            #
            item_keywords_vector = np.array(text['vector'],dtype= 'float32').tobytes()
            item_metadata[vector_field_name]=item_keywords_vector
            # HSET
            p.hset(key,mapping=item_metadata)
            p.execute()


        
        
        
    # Make query to Redis
    def query_redis(self,query,index_name, top_k=2):
        ## Creates embedding vector from user query
        embedded_query = np.array(openai.Embedding.create(
                                                    input=query,
                                                    model=config.EMBEDDINGS_MODEL,
                                                )["data"][0]['embedding'], dtype=np.float32).tobytes()

        #prepare the query
        q = Query(f'*=>[KNN {top_k} @{config.VECTOR_FIELD_NAME} $vec_param AS vector_score]').sort_by('vector_score').paging(0,top_k).return_fields('vector_score','filename','text_chunk','text_chunk_index').dialect(2) 
        params_dict = {"vec_param": embedded_query}
        #Execute the query
        results = self.r.ft(index_name).search(q, query_params = params_dict)
        return results

    # Get mapped documents from Weaviate results
    def get_redis_results(self,query,index_name):
        
        # Get most relevant documents from Redis
        query_result = self.query_redis(query,index_name)
        
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
    
    