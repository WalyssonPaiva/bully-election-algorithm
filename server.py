
from flask import Flask, request, Response
import json
import const
import requests
app = Flask(__name__)

score = 0

@app.route("/get_score", methods=['GET'])
def retrieve_score():
    global score
    return Response(json.dumps({"score": score}), mimetype='application/json', status=200)

@app.route("/update_score", methods=['POST'])
def update_score():
    global score
    new_score = int(request.json['score'])
    if new_score <= score:
        return Response(json.dumps({"error": "Score cannot be decreased or equal to current score."}), mimetype='application/json', status=400)
    score = new_score
    return Response(json.dumps({"score": score}), mimetype='application/json', status=200)

if __name__ == "__main__":
    print("Chat Server is ready...")
    app.run(host=const.CHAT_SERVER_HOST, port=const.CHAT_SERVER_PORT, debug=True)