

import requests
import json
from flask import Flask, render_template, request, redirect, url_for, send_from_directory

app = Flask(__name__)

@app.route('/')
def index():
   print('Request for index page received')
   
   return render_template('Movie_Selector2.html')

@app.route('/suggestions', methods=['POST'])
def suggestions():
    user_input = request.form['userInput']
    
    # Make a request to the OMDB API to fetch movie suggestions
    response = requests.get(f'http://www.omdbapi.com/?s={user_input}&apikey=bd6d39c9')
    data = json.loads(response.text)
    
    # Extract movie titles from the API response
    if 'Search' in data:
        movies =data['Search']
    else:
        movies = []
    return movies;
   
#    html = ''
#         for movie in movies:
#             movieTitle=movie['Title']
#             movieYear=movie['Year']
#             moviePoster=movie['Poster']
#             html += f'<p>{movieTitle} </p><p>{movieYear}</p><img src="{moviePoster}" >'
    
#     return html


if __name__ == '__main__':
    app.run()







