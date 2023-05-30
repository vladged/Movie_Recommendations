import redis
from dotenv import load_dotenv
import os
import datetime
import json
# Create a Redis client
redis_host = 'movies-recommendations.redis.cache.windows.net'
redis_port = '6380'

#movies-recommendations.redis.cache.windows.net:6380,password=53fyVxKaZHA0NDYrNpPQCGb9Pplp6wbnUAzCaH8Dw4U=,ssl=True,abortConnect=False

load_dotenv()
redis_password = os.getenv("redis_password")


def get_db():
    r = redis.Redis(host=redis_host, port=redis_port, password=redis_password,ssl=True)
    return r
# Store logs
def LogEvent(request,session,message,error_message=""):
    user_ip = request.remote_addr
    user_name = session.get('username')
    if(user_name==None):
        user_name="Not defined"
    r = get_db()
    #log_id = r.incr('log_id_counter')
    current_time = datetime.datetime.now().isoformat()

    log_item = {
       #'id':log_id,
        'username': user_name,
        'ip': user_ip,
        'time': current_time,
        'message': message,
        'errorMessage': error_message
    }
    log_json = json.dumps(log_item)
    # Store log item in Redis
    r.rpush('logs', log_json)
 
   
def SignUpUser(username,password):
    r = get_db()
    r.hset('users', username, password)
  
def fetchAllLogs(maxRows):
    r = get_db()
    all_logs = r.hgetall('logs')
    return all_logs.items()

# Retrieve logs
def fetchAllUsers(maxRows):
    r = get_db()
    all_logs = r.hget('users')
    return all_logs.items()

# Print retrieved logs
# for log_id, log_message in all_logs.items():
#     print(f"Log ID: {log_id.decode('utf-8')}, Message: {log_message.decode('utf-8')}")
 ##############################################################################################   
 
def fetchUser(username):
    r = get_db()
    user =  r.hget('users',username)
    return user
    
def LoginUser(username, password):
    
    psw =  fetchUser(username)
    if(psw==password):
        return username
    else:
        return None
    

 