
import openai
import os
#import requests
import numpy as np
import pandas as pd
from typing import Iterator
#import tiktoken
#import textract
from numpy import array, average
from Redis_Cloud.config import * 
from Redis_Cloud.redis_Cloud  import *
    
# from redis import Redis
# from redis.commands.search.query import Query
# from redis.commands.search.field import (TextField,VectorField,NumericField)
# from redis.commands.search.indexDefinition import (IndexDefinition,IndexType)

# SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# sys.path.append(os.path.dirname(SCRIPT_DIR))

def OpenAI_AnswerQuestion(question):
   
  
    redis_client = get_db()

    # filename = TextField("filename")
    # text_chunk = TextField("text_chunk")
    # file_chunk_index = NumericField("file_chunk_index")

    # define RediSearch vector fields to use HNSW index

    # text_embedding = VectorField(VECTOR_FIELD_NAME,
    #     "HNSW", {
    #         "TYPE": "FLOAT32",
    #         "DIM": VECTOR_DIM,
    #         "DISTANCE_METRIC": DISTANCE_METRIC
    #     }
    # )
    # Add all our field objects to a list to be created as an index
    # fields = [filename,text_chunk,file_chunk_index,text_embedding]

    # redis_client.ping()

    # try:
    #     redis_client.ft(INDEX_NAME).info()
    #     print("Index already exists")
    # except Exception as e:
    #     print(e)

    #openai.api_key = "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"
    # from dotenv import load_dotenv
    # load_dotenv()
    # open_ai_key = os.getenv("OPENAI_API_KEY")
    # openai.api_key = open_ai_key

    # Check that our docs have been inserted
    # print (redis_client.ft(INDEX_NAME).info()['num_docs'])

   
    #query='who helps sherlok holmes'

    result_df = get_redis_results(redis_client,question,index_name=config.INDEX_NAME)
    print (result_df.head(2))

    # Build a prompt to provide the original query, the result and ask to summarise for the user
    summary_prompt = '''Summarise this result in a bulleted list to answer the search query a customer has sent.
    Search query: SEARCH_QUERY_HERE
    Search result: SEARCH_RESULT_HERE
    Summary:
    '''
    summary_prepped = summary_prompt.replace('SEARCH_QUERY_HERE',question).replace('SEARCH_RESULT_HERE',result_df['result'][0])
    summary = openai.Completion.create(engine=config.COMPLETIONS_MODEL,prompt=summary_prepped,max_tokens=500)
    summary_prepped1 = summary_prompt.replace('SEARCH_QUERY_HERE',question).replace('SEARCH_RESULT_HERE',result_df['result'][1])
    summary1 = openai.Completion.create(engine=config.COMPLETIONS_MODEL,prompt=summary_prepped,max_tokens=500)
    
    
    # Response provided by GPT-3
    print(summary['choices'][0]['text'])
    
    
    return [result_df['result'][0],result_df['result'][1],summary['choices'][0]['text'],summary1['choices'][0]['text']]
