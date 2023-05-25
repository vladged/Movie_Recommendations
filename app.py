from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
from Open_AI_Answers import get_completion
from Prompt import Prompt
import json
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
import requests
from DatabaseOperations import *
#=========================================================================================
from flask_cors import CORS 





app = Flask(__name__)
app.secret_key = 'ztKTTabLWigNpqDk0xDzT3BlbkFJJEhAyCx0LbR4niPEMXT9'  # Replace with your own secret key
#CORS(app)

@app.route('/')
def index():
#    print('Request for index page received')
#    prompt=Prompt()
#    movies=prompt.Favorite_Movies.split(";")
    if 'username' in session:
        # User is already signed in, redirect to the main page
        LogEvent(request,session,"User Login")
        return render_template('index.html')
    else:
        # User is not signed up, redirect to the signup page
        return redirect(url_for('signup'))
   

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/getAiRecommendations', methods=['POST'])
def getAiRecommendations():
   movies=""
   for i in range (1,5):
       movieControlName='movie'+str(i)
       movies=movies+request.form.get(movieControlName)+";"
       
   if movies:
        LogEvent(request,session,"User put movies:"+movies)
        prompt=Prompt(movies)
        recommendations1=get_completion(prompt.prompt1)
        recommendations2=get_completion(prompt.prompt2)      
      
        return render_template('recommendation.html', recommendations1 = recommendations1,recommendations2 = recommendations2)
   else:
       print('Request for hello page received with blank movies list -- redirecting')
       return redirect(url_for('index'))
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
    return movies[:3];
   


# Sign Up route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        cursor = db.execute('SELECT id FROM users WHERE username = ?', (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            return 'Username already exists. Please choose a different username.'

        db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        db.commit()
        db.close()
        LogEvent(request,session,"User "+username+" Sign up:")
        return '<h2>Sign up successful! You can now <a href="/login">log in</a>.</h2>'

    return render_template('signup.html')


# Sign In route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        cursor = db.execute('SELECT id, username FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            LogEvent(request,session,"User Sign in")
            return redirect('/')
        else:
            return 'Invalid credentials. Please try again.'

    return render_template('login.html')


# Dashboard route (requires authentication)


# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


#=============================================================================
if __name__ == '__main__':
   init_db()
   app.run()