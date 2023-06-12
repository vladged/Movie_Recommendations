

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

# Set our default models and chunking size
from config1 import COMPLETIONS_MODEL, EMBEDDINGS_MODEL, CHAT_MODEL, TEXT_EMBEDDING_CHUNK_SIZE, VECTOR_FIELD_NAME


VECTOR_DIM = 1536 #len(data['title_vector'][0]) # length of the vectors
#VECTOR_NUMBER = len(data)                 # initial number of vectors
DISTANCE_METRIC = "COSINE" 
PREFIX = "starrover1"                            # prefix for the document keys
INDEX_NAME = "starrover-index"  
#VECTOR_FIELD_NAME = 'content_vector'
data_dir = 'C:\\Development\\Open_AI\\msdocs-python-flask-webapp-quickstart-main\\msdocs-python-flask-webapp-quickstart-main\\OpenAI\\data_star_rover'


#redis_db=Redis_DB(PREFIX,INDEX_NAME)

# Ignore unclosed SSL socket warnings - optional in case you get these errors
import warnings
warnings.filterwarnings(action="ignore", message="unclosed", category=ImportWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning) 
pd.set_option('display.max_colwidth', 0)

csv_files = sorted([x for x in os.listdir(data_dir) if 'DS_Store' not in x])
csv_files

from redis import Redis
from redis.commands.search.query import Query
from redis.commands.search.field import (
    TextField,
    VectorField,
    NumericField
)
from redis.commands.search.indexDefinition import (
    IndexDefinition,
    IndexType
)
from redis_Cloud  import get_db
redis_client = get_db()

filename = TextField("filename")
text_chunk = TextField("text_chunk")
file_chunk_index = NumericField("file_chunk_index")

# define RediSearch vector fields to use HNSW index

text_embedding = VectorField(VECTOR_FIELD_NAME,
    "HNSW", {
        "TYPE": "FLOAT32",
        "DIM": VECTOR_DIM,
        "DISTANCE_METRIC": DISTANCE_METRIC
    }
)
# Add all our field objects to a list to be created as an index
fields = [filename,text_chunk,file_chunk_index,text_embedding]
#docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
redis_client.ping()

try:
    redis_client.ft(INDEX_NAME).info()
    print("Index already exists")
except Exception as e:
    print(e)
    # Create RediSearch Index
    print('Not there yet. Creating')
    redis_client.ft(INDEX_NAME).create_index(
        fields = fields,
        definition = IndexDefinition(prefix=[PREFIX], index_type=IndexType.HASH)
    )

from transformers1 import handle_file_string
#transformer=Transformers(PREFIX,INDEX_NAME)
# ##
##time
#openai.organization = "vladimir.gedgafov"
from dotenv import load_dotenv
load_dotenv()
open_ai_key = os.getenv("OPENAI_API_KEY")
openai.api_key = open_ai_key

# Initialise tokenizer
tokenizer = tiktoken.get_encoding("cl100k_base")

# Process each PDF file and prepare for embedding
for csv_file in csv_files:
    
    csv_path = os.path.join(data_dir,csv_file)
    #print(pdf_path)
    
    # Extract the raw text from each PDF using textract
    try:
        text = textract.process(csv_path, encoding='UTF-8')
    except Exception as e:
        print(e)
       
    
    # Chunk each document, embed the contents and load to Redis
    #handle_file_string((csv_file,text.decode("utf-8")),tokenizer,redis_client,PREFIX)
    handle_file_string((csv_file,text.decode("utf-8")),tokenizer,redis_client,VECTOR_FIELD_NAME,PREFIX)


print (redis_client.ft(INDEX_NAME).info()['num_docs'])

from database1 import get_redis_results


f1_query='what is Sherlock Holmes occupation'

result_df = get_redis_results(redis_client,f1_query,index_name=INDEX_NAME)
print (result_df.head(2))

# Build a prompt to provide the original query, the result and ask to summarise for the user
summary_prompt = '''Summarise this result in a bulleted list to answer the search query a customer has sent.
Search query: SEARCH_QUERY_HERE
Search result: SEARCH_RESULT_HERE
Summary:
'''
summary_prepped = summary_prompt.replace('SEARCH_QUERY_HERE',f1_query).replace('SEARCH_RESULT_HERE',result_df['result'][0])
summary = openai.Completion.create(engine=COMPLETIONS_MODEL,prompt=summary_prepped,max_tokens=500)
# Response provided by GPT-3
print(summary['choices'][0]['text'])

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
question = 'How can you help me'


completion = openai.ChatCompletion.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "user", "content": question}
  ]
)
print(f"{completion['choices'][0]['message']['role']}: {completion['choices'][0]['message']['content']}")

# %%
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

    def _get_assistant_response(self, prompt):
        
        try:
            completion = openai.ChatCompletion.create(
              model="gpt-3.5-turbo",
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
    
    def __init__(self):
        self.conversation_history = []  

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
        search_content = get_redis_results(redis_client,latest_question,INDEX_NAME)['result'][0]
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


