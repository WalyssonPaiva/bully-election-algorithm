
import queue
import sys
import threading
from time import sleep
from flask import Flask, request, Response
import json
import const
import requests
import os
import logging
# ----------------- Coordinator functions -----------------

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app = Flask(__name__)

# import of coordinator functions/routes
from coordinator_functions import coordinator, get_user
app.register_blueprint(coordinator, url_prefix="/")
# ---------------------------------------------------------

# ------------------- Client ------------------------------
permission = False # global variable to control my permission
coordinator = False # define if I am the coordinator
coordnator_name = "" # coordinator name, to get this IP and PORT to request permissions

# ------------------ mutual exclusion functions ---------------------
@app.route("/give_permission", methods=['POST']) # this route receive a response from coordinator giving permission (like a webhook)
def give_permission():
    global permission
    permission_from_coordinator = request.json['permission']
    if permission_from_coordinator:
        permission = True
        print("Permission granted")
    return {} 


def wait_for_permission(): # this function will ask for permission to coordinator and wait for it
    global permission
    if not permission:
        requests.post(f"{get_user(coordnator_name)}/get_permission", json={"user": i_am})
    while permission == False:
        sleep(1)
        print("Waiting for permission...")
    return True

def release_permission(): # this function will release permission to coordinator after finishing use the resource (score)
    global permission
    permission = False
    requests.post(f"{get_user(coordnator_name)}/release_permission", json={"user": i_am})
# ------------------ end of mutual exclusion functions ---------------------

# ------------------ election functions ---------------------

def request_election():
    election_response = []
    for user in const.registry:
        if user != i_am:
            (ip, port, id) = const.registry[user]
            if id > const.registry[i_am][2]:
                try:
                    response = requests.post(f"http://{ip}:{port}/election", json={"user": i_am})
                    election_response.append(response.json()['response'])
                except:
                    pass
    if len(election_response) == 0:
        print("I am the new coordinator")
        global coordinator
        coordinator = True
        global coordnator_name
        coordnator_name = i_am
        for user in const.registry:
            if user != i_am:
                (ip, port, id) = const.registry[user]
                try:
                    response = requests.post(f"http://{ip}:{port}/election_result", json={"coordinator": i_am})
                except:
                    pass
    
@app.route("/election", methods=['POST'])
def election():
    user = request.json['user']
    threading.Thread(target=request_election).start()
    return json.dumps({"response": "ok"})

@app.route("/election_result", methods=['POST'])
def election_result():
    global coordnator_name
    new_coordinator = request.json['coordinator']
    print(f"New coordinator: {new_coordinator}")
    coordnator_name = new_coordinator
    return json.dumps({"response": "ok"})

def request_score():
    response = requests.get(f"http://{const.CHAT_SERVER_HOST}:{const.CHAT_SERVER_PORT}/get_score")
    print(f"current score: {response.json()['score']}")

def start_server(i_am):
    (ip, port, id) = const.registry[i_am]
    app.run(host=ip, port=port)

def update_score():
    request_score()
    new_score = input("Enter new score: ")
    try:
        response = requests.post(f"http://{const.CHAT_SERVER_HOST}:{const.CHAT_SERVER_PORT}/update_score", json={"score": new_score})
        print(f"new score: {response.json()['score']}")
        print("Score updated successfully")
    except:
        print(response.json()['error'])

options = {
    "1": request_score,
    "2": update_score,
    "3": exit
}

if __name__ == "__main__":
    i_am = str(sys.argv[1])
    coordnator_name = str(sys.argv[2])

    if i_am == coordnator_name:
        coordinator = True
        print("I am coordinator")
    threading.Thread(target=start_server, args=(i_am,), daemon=True).start()
    while True:
        print("--------------------------------------------------------------------------------")
        print("Insert the number of the option you want to execute:")
        print("1 - Get Score")
        print("2 - Update Score")
        print("3 - Close")
        option = input("Choose an option: ")
        print("--------------------------------------------------------------------------------")
        if option not in options:
            print("Invalid option")
            continue
        os.system('cls||clear')
        try:
            wait_for_permission()
            options[option]()
            release_permission()
        except:
            request_election()