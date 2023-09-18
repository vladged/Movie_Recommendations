import openai
import os
import sys

# from typing import Iterator
# #import tiktoken
# #import textract
# from numpy import array, average
import redis

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)

sys.path.append(ROOT_DIR)

from  Redis_Cloud.Redis_Utils import *

def OpenAI_AnswerQuestion(redis_conn,question,index_name,COMPLETIONS_MODEL ="text-davinci-003",CHAT_MODEL = 'gpt-3.5-turbo'):  #COMPLETIONS_MODEL = "text-davinci-003" ,    ):
    result_df =get_redis_results(redis_conn,question,index_name)
   
    summary_prompt = '''Summarise this result in a bulleted list to answer the search query a customer has sent.
    Search query: SEARCH_QUERY_HERE
    Search result: SEARCH_RESULT_HERE
    Summary:
    '''
    summary_prepped = summary_prompt.replace('SEARCH_QUERY_HERE',question).replace('SEARCH_RESULT_HERE',result_df['result'][0])
    summary = openai.Completion.create(engine=COMPLETIONS_MODEL,prompt=summary_prepped,max_tokens=500)
    summary_chat = response = openai.ChatCompletion.create(
    model=CHAT_MODEL,
    messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": question},
            {"role": "assistant", "content": result_df['result'][0]}
          
           # {"role": "user", "content": "Where was it played?"}
        ]
    )
    return result_df['result'][0],summary,summary_chat #[result_df['result'][0],result_df['result'][1],summary['choices'][0]['text'],summary1['choices'][0]['text']]

r = redis.Redis(host="localhost", port="6379", password="")
#answer=OpenAI_AnswerQuestion(r,"why knights templar were destroyed",'Prophet-index')
#answer,answer_chat=OpenAI_AnswerQuestion(r,"Why did Russia invade Ukraine?",'YevgenyPrigozhin-index')
#search_result,answer,answer_chat=OpenAI_AnswerQuestion(r,"Why did Russia invade Ukraine?",'RussianinvasionofUkraine-index')
search_result,answer,answer_chat=OpenAI_AnswerQuestion(r,"What is the best way to help ukraine to win the war?",'RussianinvasionofUkraine-index')
print(search_result,answer,"/n",answer_chat)
