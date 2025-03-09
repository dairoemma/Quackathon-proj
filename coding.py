from flask import Flask, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, JWTManager, decode_token
import redis
import os
import pymongo
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import certifi


app = Flask(__name__)

app.config['JWT_SECRET_KEY'] = 'my_secret_key'
jwt = JWTManager(app)
app.config['SESSION_TYPE'] = redis
app.config['SESSION_PERMANENT'] = False
CORS(app)
red = redis.StrictRedis(host='35.192.222.77', port=6379, db=0, decode_responses=True)
socket = SocketIO(app, cors_allowed_origin="*")

uni_dict = {}
user_dict = {}


def get_mongodb_value():
    client = pymongo.MongoClient("mongodb+srv://dairotomiwa7:Kawhi7@cluster-db.jws4d.mongodb.net/", tlsCAFile=certifi.where())
    db = client["Practice-database"]
    return db


def fetch_mongodb_uni_details():
    global uni_dict
    db = get_mongodb_value()
    uni_details = db.Uni.find({}, {"_id": 0})
    uni_dict = {uni["name"]: uni for uni in uni_details}


def fetch_mongodb_user_details():
    global user_dict
    db = get_mongodb_value()
    user_details =  db.user.find({}, {"_id": 0})
    user_dict = {user["name"]: user for user in user_details}


@app.route('/app_authenticate_user', methods=['POST'])
def app_authenticate_user():
    data = request.json
    user_name = data['user_name']
    password = data['password']
    fetch_mongodb_user_details()

    for user_n, user_details in user_dict.items():
        if user_name == user_n and user_details["password"] == password:
            print({"message": "Access Granted"})
            access_token = create_access_token(identity=user_name)
            return jsonify(access_token=access_token), 200
        else:
            return jsonify({"message": "Invalid Credentials, Sign up "}), 401


@app.route('/app_add_user', methods=['POST'])
def app_add_user():
    db = get_mongodb_value()
    data = request.json
    user_name = data['user_name']
    password = data['password']
    level_of_study = data['level_of_study']
    course = data['course']
    location = data['location']

    fetch_mongodb_user_details()

    if user_name not in user_dict:
        db.user.insert_one({"name": user_name, "password": password, "level": level_of_study,
                            "degree": course, "location": location})
        socket.emit('message', {"message": f"{user_name} added"}, broadcast=True)
        return jsonify({"message": "User successfully created "}), 201
    else:
        return jsonify({"Message": "Username already exists"}), 400


@app.route('/app_user_profile', methods=['GET'])
@jwt_required()
def app_user_profile():
    user_name = get_jwt_identity()
    fetch_mongodb_user_details()

    if user_name:
        print({"message": "Access Granted"})
        for user_n, user_details in user_dict.items():
            if user_name == user_n:
                return jsonify(user_details), 200
            else:
                return jsonify({"user not present"}), 400
    else:
        return jsonify({"Invalid details"}), 401


@app.route('/app_get_users', methods=['GET'])
def app_get_user():
    fetch_mongodb_user_details()
    return jsonify(user_dict), 200


@app.route('/app_search_users', methods=['GET'])
def app_search_user():
    data = request.json
    user_choice = data['user_choice']
    fetch_mongodb_user_details()

    for user_n, user_details in user_dict.items():
        if user_choice == user_n:
            return jsonify(user_details), 200
        else:
            return jsonify({"message": "user not found"}), 404


@app.route('/app_delete_user', methods=['POST'])
@jwt_required()
def app_delete_user():
    user_name = get_jwt_identity()
    fetch_mongodb_user_details()
    db = get_mongodb_value()

    if user_name:
        if user_name in user_dict:
            db.user.delete_one({"name": user_name})
            return jsonify({"message": "User successfully deleted"}), 200
        else:
            return jsonify({"message": "User doesn't exist"}), 404
    else:
        return jsonify({"message": "Invalid Credentials, Access Denied!!"}), 401


@app.route('/app_get_universities', methods=['GET'])
def app_get_university():
    fetch_mongodb_uni_details()
    return jsonify(uni_dict), 200


@app.route('/app_view_university', methods=['GET'])
def app_view_university():
    data = request.json
    uni_choice = data['uni_choice']
    fetch_mongodb_uni_details()

    for uni, uni_details in uni_dict.items():
        if uni_choice == uni:
            return jsonify(uni_details)
        else:
            return jsonify({"message": "University not found"}), 400


@socket.on('connect')
def socket_on_connect():
    request_token = request.args.get('token')

    if request_token:
        decoded_token = decode_token(request_token)
        user_id = decoded_token['identity']
        room = join_room(user_id)

        red.set(user_id, room)
    else:
        print({"message": "Invalid access"})


@socket.on("message")
def handle_message(msg):
    message = msg['msg']
    room = msg['room']
    request_token = request.args.get('token')
    if request_token:
        decoded_token = decode_token(request_token)
        user_name = decoded_token['identity']
        validate_room = red.get(room)
        validate_user = red.get(user_name)
        if validate_user:
            if validate_room:
                emit(message, to=room)
            else:
                print({"message": "room not found"})
        else:
            print({"message": "Invalid user"})

    else:
        print({"message": "Invalid  access"})


@socket.on("leave_room")
def leave_room(ur):
    user_room = ur['ur']
    fetch_mongodb_user_details()

    if user_room in user_dict:
        print({"message": "Can't delete user chat"})
    else:
        leave_room(user_room)
        print({"message": "successfully deleted user chat"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 1000))
    socket.run(app, debug=True, host="0.0.0.0", port=port,allow_unsafe_werkzeug=True)
