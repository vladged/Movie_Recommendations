import openai
import os
#import requests
import numpy as np
import pandas as pd
from typing import Iterator
#import tiktoken
#import textract
from numpy import array, average
import sys
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

# from Redis_Cloud.config import *
# from Redis_Cloud.redis_Cloud import *
from dotenv import load_dotenv
import os

load_dotenv()
open_ai_key = os.getenv("OPENAI_API_KEY")
openai.api_key = open_ai_key

# redis_helper=Redis_helper(redis_host='localhost',port='6379',redis_password_name='')


# print (redis_client.ft(INDEX_NAME).info()['num_docs'])


# f1_query='how marin iden died'

# result_df = get_redis_results(redis_client,f1_query,index_name=INDEX_NAME)
# print (result_df.head(2))

# # Build a prompt to provide the original query, the result and ask to summarise for the user
# summary_prompt = '''Summarise this result in a bulleted list to answer the search query a customer has sent.
# Search query: SEARCH_QUERY_HERE
# Search result: SEARCH_RESULT_HERE
# Summary:
# '''
# summary_prepped = summary_prompt.replace('SEARCH_QUERY_HERE',f1_query).replace('SEARCH_RESULT_HERE',result_df['result'][0])
# summary = openai.Completion.create(engine=COMPLETIONS_MODEL,prompt=summary_prepped,max_tokens=500)
# # Response provided by GPT-3
# print(summary['choices'][0]['text'])

# %% [markdown]
# ### Search
# 
# Now that we've got our knowledge embedded and stored in Redis, we can  create an internal search application. 
# Its not sophisticated but it'll get the job done for us.
# 
# In the directory containing this app, execute ```streamlit run search.py```. This will open up a 
# Streamlit app in your browser where you can ask questions of your embedded data.
# 
# __Example Questions__:
# - what is the cost cap for a power unit in 2023
# - what should competitors include on their application form

# %% [markdown]
# ## Build your moat
# 
# The Q&A was useful, but fairly limited in the complexity of interaction we can have - if the user asks a sub-optimal question, 
# there is no assistance from the system to prompt them for more info or conversation to lead them down the right path.
# 
# For the next step we'll make a Chatbot using the Chat Completions endpoint, which will:
# - Be given instructions on how it should act and what the goals of its users are
# - Be supplied some required information that it needs to collect
# - Go back and forth with the customer until it has populated that information
# - Say a trigger word that will kick off semantic search and summarisation of the response
# 
# For more details on our Chat Completions endpoint and how to interact with it, please check out the docs [here](https://platform.openai.com/docs/guides/chat).

# %% [markdown]
# ### Framework
# 
# This section outlines a basic framework for working with the API and storing context of previous conversation "turns". 
# Once this is established, we'll extend it to use our retrieval endpoint.

# %%
# A basic example of how to interact with our ChatCompletion endpoint
# It requires a list of "messages", consisting of a "role" (one of system, user or assistant) and "content"
# question = 'How can you help me'


# completion = openai.ChatCompletion.create(
#   model=CHAT_MODEL ,
#   messages=[
#     {"role": "user", "content": question}
#   ]
# )
# print(f"{completion['choices'][0]['message']['role']}: {completion['choices'][0]['message']['content']}")

# # %%
from termcolor import colored

# A basic class to create a message as a dict for chat
class Message:
    
    
    def __init__(self,role,content):
        
        self.role = role
        self.content = content
        
    def message(self):
        
        return {"role": self.role,"content": self.content}
        
# Our assistant class we'll use to converse with the bot
class Assistant:
    
    def __init__(self):
        self.conversation_history = []

    def _get_assistant_response(self, prompt,CHAT_MODEL='gpt-3.5-turbo'):
        
        try:
            completion = openai.ChatCompletion.create(
              model=CHAT_MODEL,
              messages=prompt
            )
            
            response_message = Message(completion['choices'][0]['message']['role'],completion['choices'][0]['message']['content'])
            return response_message.message()
            
        except Exception as e:
            
            return f'Request failed with exception {e}'

    def ask_assistant(self, next_user_prompt, colorize_assistant_replies=True):
        [self.conversation_history.append(x) for x in next_user_prompt]
        assistant_response = self._get_assistant_response(self.conversation_history)
        self.conversation_history.append(assistant_response)
        return assistant_response
            
        
    def pretty_print_conversation_history(self, colorize_assistant_replies=True):
        for entry in self.conversation_history:
            if entry['role'] == 'system':
                pass
            else:
                prefix = entry['role']
                content = entry['content']
                output = colored(prefix +':\n' + content, 'green') if colorize_assistant_replies and entry['role'] == 'assistant' else prefix +':\n' + content
                print(output)

# %%
# Initiate our Assistant class
conversation = Assistant()

# Create a list to hold our messages and insert both a system message to guide behaviour and our first user question
messages = []
system_message = Message('system','You are a helpful business assistant who has innovative ideas')
user_message = Message('user','What can you do to help me')
messages.append(system_message.message())
messages.append(user_message.message())
messages

# %%
# Get back a response from the Chatbot to our question
response_message = conversation.ask_assistant(messages)
print(response_message['content'])

# %%
next_question = 'Tell me more about option 2'

# Initiate a fresh messages list and insert our next question
messages = []
user_message = Message('user',next_question)
messages.append(user_message.message())
response_message = conversation.ask_assistant(messages)
print(response_message['content'])

# %%
# Print out a log of our conversation so far

conversation.pretty_print_conversation_history()

# %% [markdown]
# ### Knowledge retrieval
# 
# Now we'll extend the class to call a downstream service when a stop sequence is spoken by the Chatbot.
# 
# The main changes are:
# - The system message is more comprehensive, giving criteria for the Chatbot to advance the conversation
# - Adding an explicit stop sequence for it to use when it has the info it needs
# - Extending the class with a function ```_get_search_results``` which sources Redis results

# %%
# Updated system prompt requiring Question and Year to be extracted from the user
system_prompt = '''
You are a helpful Formula 1 knowledge base assistant. You need to capture a Question and Year from each customer.
The Question is their query on Formula 1, and the Year is the year of the applicable Formula 1 season.
If they haven't provided the Year, ask them for it again.
Once you have the Year, say "searching for answers".

Example 1:

User: I'd like to know the cost cap for a power unit

Assistant: Certainly, what year would you like this for?

User: 2023 please.

Assistant: Searching for answers.
'''

# New Assistant class to add a vector database call to its responses
class RetrievalAssistant:
    
    def __init__(self,INDEX_NAME):
        self.conversation_history = []  
        self.index_name=INDEX_NAME

    def _get_assistant_response(self, prompt):
        
        try:
            completion = openai.ChatCompletion.create(
              model=CHAT_MODEL,
              messages=prompt,
              temperature=0.1
            )
            
            response_message = Message(completion['choices'][0]['message']['role'],completion['choices'][0]['message']['content'])
            return response_message.message()
            
        except Exception as e:
            
            return f'Request failed with exception {e}'
    
    # The function to retrieve Redis search results
    def _get_search_results(self,prompt):
        latest_question = prompt
        search_content = self.get_redis_results(latest_question,self.index_name)['result'][0]
        return search_content
        

    def ask_assistant(self, next_user_prompt):
        [self.conversation_history.append(x) for x in next_user_prompt]
        assistant_response = self._get_assistant_response(self.conversation_history)
        
        # Answer normally unless the trigger sequence is used "searching_for_answers"
        if 'searching for answers' in assistant_response['content'].lower():
            question_extract = openai.Completion.create(model=COMPLETIONS_MODEL,prompt=f"Extract the user's latest question and the year for that question from this conversation: {self.conversation_history}. Extract it as a sentence stating the Question and Year")
            search_result = self._get_search_results(question_extract['choices'][0]['text'])
            
            # We insert an extra system prompt here to give fresh context to the Chatbot on how to use the Redis results
            # In this instance we add it to the conversation history, but in production it may be better to hide
            self.conversation_history.insert(-1,{"role": 'system',"content": f"Answer the user's question using this content: {search_result}. If you cannot answer the question, say 'Sorry, I don't know the answer to this one'"})
            #[self.conversation_history.append(x) for x in next_user_prompt]
            
            assistant_response = self._get_assistant_response(self.conversation_history)
            print(next_user_prompt)
            print(assistant_response)
            self.conversation_history.append(assistant_response)
            return assistant_response
        else:
            self.conversation_history.append(assistant_response)
            return assistant_response
            
        
    def pretty_print_conversation_history(self, colorize_assistant_replies=True):
        for entry in self.conversation_history:
            if entry['role'] == 'system':
                pass
            else:
                prefix = entry['role']
                content = entry['content']
                output = colored(prefix +':\n' + content, 'green') if colorize_assistant_replies and entry['role'] == 'assistant' else prefix +':\n' + content
                #prefix = entry['role']
                print(output)

# %%
conversation = RetrievalAssistant()
messages = []
system_message = Message('system',system_prompt)
user_message = Message('user','How can a competitor be disqualified from competition')
messages.append(system_message.message())
messages.append(user_message.message())
response_message = conversation.ask_assistant(messages)
response_message

# %%
messages = []
user_message = Message('user','For 2023 please.')
messages.append(user_message.message())
response_message = conversation.ask_assistant(messages)
#response_message

# %%
conversation.pretty_print_conversation_history()

# %% [markdown]
# ### Chatbot
# 
# Now we'll put all this into action with a real (basic) Chatbot.
# 
# In the directory containing this app, execute ```streamlit run chat.py```. This will open up a Streamlit app in your browser where you can ask questions of your embedded data. 
# 
# __Example Questions__:
# - what is the cost cap for a power unit in 2023
# - what should competitors include on their application form
# - how can a competitor be disqualified

# %% [markdown]
# ### Consolidation
# 
# Over the course of this notebook you have:
# - Laid the foundations of your product by embedding our knowledge base
# - Created a Q&A application to serve basic use cases
# - Extended this to be an interactive Chatbot
# 
# These are the foundational building blocks of any Q&A or Chat application using our APIs - these are your starting point, and we look forward to seeing what you build with them!


