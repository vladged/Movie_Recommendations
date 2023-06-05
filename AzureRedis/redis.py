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
# def LogEvent(request,session,message,error_message=""):
#     user_ip = request.remote_addr
#     user_name = session.get('username')
#     if(user_name==None):
#         user_name="Not defined"
#     r = get_db()
#     #log_id = r.incr('log_id_counter')
#     current_time = datetime.datetime.now().isoformat()

#     log_item = {
#        #'id':log_id,
#         'username': user_name,
#         'ip': user_ip,
#         'time': current_time,
#         'message': message,
#         'errorMessage': error_message
#     }
#     log_json = json.dumps(log_item)
#     # Store log item in Redis
#     r.rpush('logs', log_json)
    
def LogEvent(request, session, message):
    r = get_db();
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    ip_address = request.remote_addr
    username = session.get('username', 'Not defined')
    log_entry = f"{current_time} | IP: {ip_address} | Username: {username} | Message: {message}"
    r.rpush('logs1', log_entry) 
   
def SignUpUser(username, password):
    r = get_db()
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    user_data = {
        'user_id': str(username),
        'password': str(password),
        'datetime': str(current_time)
    }
    # Convert None values to empty string
    user_data = {k: v if v is not None else "" for k, v in user_data.items()}
    user_data_json = json.dumps(user_data)
    r.hset('users1', username, user_data_json)
  
def fetchAllLogs(maxRows):
    r = get_db()
    #all_logs = r.hgetall('logs1')
    items = r.lrange('logs1', -maxRows, -1)
    items.reverse()
    return items

# Retrieve logs
def fetchAllUsers(maxRows):
    r = get_db()
    all_logs = r.hget('users1')
    return all_logs.items()

# Print retrieved logs
# for log_id, log_message in all_logs.items():
#     print(f"Log ID: {log_id.decode('utf-8')}, Message: {log_message.decode('utf-8')}")
 ##############################################################################################   
 
# def fetchUser(username):
#     r = get_db()
#     user =  r.hget('users1',username)
#     return user
def fetchUser(user_id):
    r = get_db()
    user_data = r.hget('users1', user_id)
    if user_data:
        return eval(user_data)  # Convert string representation back to a dictionary
    return None   
def LoginUser(username, password):
    user_data=fetchUser(username)
    psw =  user_data['password']
    if(psw==password):
        return username
    else:
        return None
    

 