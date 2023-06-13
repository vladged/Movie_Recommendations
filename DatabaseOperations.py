
from AzureRedis.config import *
import sqlite3
#from flask import request, session

# Create a SQLite database connection
def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db
def LogEvent(request,session,message):
    user_ip = request.remote_addr
    user_name = session.get('username')
    if(user_name==None):
        user_name="Not defined"
    db = get_db()
    db.execute("INSERT INTO Log ( user,message, IP) VALUES ('"+user_name+"','"+message+"','"+user_ip+"' );")
    
    db.commit()
    db.close()
    
# Initialize the database with user table
def init_db():
    db = get_db()
    db.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT)')
    
    db.commit()
    db.close()

def fetchUserCursor(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    user=cursor.fetchone()
    db.close()
    return user
def fetchLoginCursor(username,password):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id, username FROM users WHERE username = ? AND password = ?', (username, password))
    user = cursor.fetchone()
    return user
def SignUpUser(username,password):
    db = get_db()
    db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
    db.commit()
    db.close()
    
def fetchLogCursor(maxRows):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('select timestamp,message,IP,user,error from log order by timestamp desc limit ?', (maxRows,))
    logs=cursor.fetchall()
    db.close()
    return logs
def fetchUsersCursor():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('select username from users')
    users=cursor.fetchall()
    db.close()
    return users