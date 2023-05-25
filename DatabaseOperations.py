
from config import *
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
