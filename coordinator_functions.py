import queue
from flask import Blueprint, request, Response
import requests
import const

coordinator = Blueprint('coordinator', __name__)

wait_queue = queue.Queue()
blocked = False


@coordinator.route("/get_permission", methods=['POST'])
def get_permission():
    global permission_queue
    global blocked
    user = request.json['user']
    if blocked:
        wait_queue.put(user)
    else:
        blocked = True
        requests.post(get_user(user) + "/give_permission", json={"permission": True})
    return {}
 

@coordinator.route("/release_permission", methods=['POST'])
def release_permission_coordinator():
    global permission_queue
    global blocked
    blocked = False
    if not wait_queue.empty():
        user = wait_queue.get()
        blocked = True
        requests.post(f"{get_user(user)}/give_permission", json={"permission": True})
    return {}

def get_user(user):
    (ip, port, id) = const.registry[user]
    return f"http://{ip}:{port}"