import json
import redis
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

TTL_SECONDS = 1800
MAX_MESSAGES = 10

def key(session_id: str) -> str:  #generating unique redis key
    return f"chat:{session_id}"

def add_message(session_id: str, role: str, content: str) -> None: #
    k = key(session_id) 
    r.rpush(k, json.dumps({"role": role, "content": content})) 
    r.ltrim(k, -MAX_MESSAGES, -1)   # keep only the last N messages
    r.expire(k, TTL_SECONDS) 
    
def get_history(session_id: str) -> list[dict[str, str]]: #retrieves all the stored messages for particular session
    return [json.loads(m) for m in r.lrange(key(session_id), 0, -1)]

