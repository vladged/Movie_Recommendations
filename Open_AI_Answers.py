# Iterative Prompt Develelopment
#In this lesson, you'll iteratively analyze and refine your prompts to generate marketing copy from a product fact sheet.

## Setup

import openai
import os
from Prompt import *
from dotenv import load_dotenv
#from config import *

""" from dotenv import load_dotenv, find_dotenv
_ = load_dot env(find_dotenv()) # read local .env file
"""

#openai.api_key  = API_KEY
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

def get_completion(prompt):
    response = openai.Completion.create(
    engine='text-davinci-003',
    prompt=prompt,
    max_tokens=500,
    n=1,
    stop=None,
    temperature=0.7,
    top_p=1.0,
    frequency_penalty=0.0,
    presence_penalty=0.0
    )
    recommendations = response.choices[0].text.strip()
    recommendations_arr = response.choices[0].text.strip().split("\n")
# Print the recommended movies with descriptions
    result=""
 #   formatted_recommendations = "<br>".join(f"<p>{r}</p>" for r in recommendations_arr)
    for i, recommendation in enumerate(recommendations_arr, start=1):
        result=result+f"{recommendation}<br/>"
        #formatted_recommendations = "<br>".join(result)
    
    return result




