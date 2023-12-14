import redis
import json
from typing import Dict


r = redis.Redis(host='localhost', port=6379, decode_responses=True)


def load_from_redis(key="all_threads") -> Dict:
    threads = r.get("all_threads")
    return json.loads(threads) if threads else {}


def save_to_redis(threads) -> int:
    threads = json.dumps(threads)
    return r.set("all_threads", threads)


def nuke_redis() -> int:
    return r.delete("all_threads")
