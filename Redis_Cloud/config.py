import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

COMPLETIONS_MODEL = "text-davinci-003"
EMBEDDINGS_MODEL = "text-embedding-ada-002"
CHAT_MODEL = 'gpt-3.5-turbo'
TEXT_EMBEDDING_CHUNK_SIZE=300
VECTOR_FIELD_NAME='content_vector'
VECTOR_DIM = 1536 #len(data['title_vector'][0]) # length of the vectors
 #VECTOR_NUMBER = len(data)                 # initial number of vect
DISTANCE_METRIC = "COSINE"                # distance metric for the vectors (ex. COSININDEX_NAME = "f1-index"           # name of the search index
PREFIX = "JackLondon"                            # prefix for the document keys
INDEX_NAME = "JackLondon-index" 
DATABASE = 'database.db'
    
