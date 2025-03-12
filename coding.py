from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import redis
import jwt
import datetime
from passlib.context import CryptContext
from pydantic import BaseModel

# Load environment variables
load_dotenv()
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "my_secret_key")

# Initialize FastAPI app
app = FastAPI(title="University API", description="A FastAPI implementation of the Flask API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis setup
redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

# MongoDB setup
def get_mongodb_client():
    mongo_uri = os.getenv("MONGO_URI")
    client = MongoClient(mongo_uri)
    return client["Practice-database"]

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Token functions
def create_access_token(identity: str):
    """Generate JWT access token"""
    expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    token = jwt.encode({"sub": identity, "exp": expiration}, SECRET_KEY, algorithm="HS256")
    return token

def verify_token(token: str):
    """Verify JWT token"""
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# User authentication model
class UserAuth(BaseModel):
    user_name: str
    password: str

# Root endpoint
@app.get("/")
def root():
    """Root endpoint to indicate the API is running."""
    return {"message": "Welcome to the University API"}

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint to verify API status."""
    return {"status": "healthy"}

@app.post("/app_authenticate_user")
def app_authenticate_user(user: UserAuth):
    """Authenticate user and return a JWT token."""
    db = get_mongodb_client()
    user_details = db.user.find_one({"name": user.user_name}, {"_id": 0})
    
    if user_details and user_details["password"] == user.password:
        access_token = create_access_token(identity=user.user_name)
        return {"access_token": access_token}
    
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Credentials, Sign up")

@app.post("/app_add_user")
def app_add_user(user: UserAuth):
    """Add a new user to the database."""
    db = get_mongodb_client()
    existing_user = db.user.find_one({"name": user.user_name})
    
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    
    db.user.insert_one({"name": user.user_name, "password": user.password})
    redis_client.publish('message', f"{user.user_name} added")
    return {"message": "User successfully created"}

@app.get("/app_user_profile")
def app_user_profile(token: str):
    """Get user profile details."""
    user_name = verify_token(token)
    db = get_mongodb_client()
    user_details = db.user.find_one({"name": user_name}, {"_id": 0})
    
    if user_details:
        return user_details
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

@app.get("/app_get_users")
def app_get_users():
    """Retrieve all users from the database."""
    db = get_mongodb_client()
    users = list(db.user.find({}, {"_id": 0}))
    return users

@app.post("/app_delete_user")
def app_delete_user(token: str):
    """Delete the authenticated user from the database."""
    user_name = verify_token(token)
    db = get_mongodb_client()
    result = db.user.delete_one({"name": user_name})
    
    if result.deleted_count:
        return {"message": "User successfully deleted"}
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User doesn't exist")

@app.get("/app_get_universities")
def app_get_universities():
    """Retrieve university details from the database."""
    db = get_mongodb_client()
    universities = list(db.Uni.find({}, {"_id": 0}))
    return universities

@app.get("/app_view_university")
def app_view_university(uni_choice: str):
    """Retrieve details of a specific university."""
    db = get_mongodb_client()
    uni_details = db.Uni.find_one({"name": uni_choice}, {"_id": 0})
    
    if uni_details:
        return uni_details
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="University not found")

# Run the application if executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



# from flask import Flask, request, jsonify
# from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, JWTManager, decode_token
# from redis import Redis
# from pymongo import MongoClient
# import os
# from dotenv import load_dotenv
# from flask_cors import CORS
# from flask_socketio import SocketIO, emit, join_room, leave_room
# import certifi

# load_dotenv()


# app = Flask(__name__)

# app.config['JWT_SECRET_KEY'] = 'my_secret_key'
# jwt = JWTManager(app)
# app.config['SESSION_TYPE'] = Redis
# app.config['SESSION_PERMANENT'] = False
# CORS(app)
# redis = Redis(host='redis', port=6379, db=0, decode_responses=True)
# redis = Redis(host='redis', port=6379, db=0, decode_responses=True)
# socket = SocketIO(app, cors_allowed_origin="*")

# uni_dict = {}
# user_dict = {}


# def get_mongodb_value():
#     mongo_uri = os.getenv("MONGO_URI")
#     client = MongoClient(mongo_uri)
#     db = client["Practice-database"]
#     return db



# def fetch_mongodb_uni_details():
#     global uni_dict
#     db = get_mongodb_value()
#     uni_details = db.Uni.find({}, {"_id": 0})
#     uni_dict = {uni["name"]: uni for uni in uni_details}


# def fetch_mongodb_user_details():
#     global user_dict
#     db = get_mongodb_value()
#     user_details =  db.user.find({}, {"_id": 0})
#     user_dict = {user["name"]: user for user in user_details}


# @app.route('/app_authenticate_user', methods=['POST'])
# def app_authenticate_user():
#     data = request.json
#     user_name = data['user_name']
#     password = data['password']
#     fetch_mongodb_user_details()

#     for user_n, user_details in user_dict.items():
#         if user_name == user_n and user_details["password"] == password:
#             print({"message": "Access Granted"})
#             access_token = create_access_token(identity=user_name)
#             return jsonify(access_token=access_token), 200
#         else:
#             return jsonify({"message": "Invalid Credentials, Sign up "}), 401


# @app.route('/app_add_user', methods=['POST'])
# def app_add_user():
#     db = get_mongodb_value()
#     data = request.json
#     user_name = data['user_name']
#     password = data['password']
#     level_of_study = data['level_of_study']
#     course = data['course']
#     location = data['location']

#     fetch_mongodb_user_details()

#     if user_name not in user_dict:
#         db.user.insert_one({"name": user_name, "password": password, "level": level_of_study,
#                             "degree": course, "location": location})
#         socket.emit('message', {"message": f"{user_name} added"}, broadcast=True)
#         return jsonify({"message": "User successfully created "}), 201
#     else:
#         return jsonify({"Message": "Username already exists"}), 400


# @app.route('/app_user_profile', methods=['GET'])
# @jwt_required()
# def app_user_profile():
#     user_name = get_jwt_identity()
#     fetch_mongodb_user_details()

#     if user_name:
#         print({"message": "Access Granted"})
#         for user_n, user_details in user_dict.items():
#             if user_name == user_n:
#                 return jsonify(user_details), 200
#             else:
#                 return jsonify({"message": "user not present"}), 400
#     else:
#         return jsonify({"Invalid details"}), 401


# @app.route('/app_get_users', methods=['GET'])
# def app_get_user():
#     fetch_mongodb_user_details()
#     return jsonify(user_dict), 200


# @app.route('/app_search_users', methods=['GET'])
# def app_search_user():
#     data = request.json
#     user_choice = data['user_choice']
#     fetch_mongodb_user_details()

#     for user_n, user_details in user_dict.items():
#         if user_choice == user_n:
#             return jsonify(user_details), 200
#         else:
#             return jsonify({"message": "user not found"}), 404


# @app.route('/app_delete_user', methods=['POST'])
# @jwt_required()
# def app_delete_user():
#     user_name = get_jwt_identity()
#     fetch_mongodb_user_details()
#     db = get_mongodb_value()

#     if user_name:
#         if user_name in user_dict:
#             db.user.delete_one({"name": user_name})
#             return jsonify({"message": "User successfully deleted"}), 200
#         else:
#             return jsonify({"message": "User doesn't exist"}), 404
#     else:
#         return jsonify({"message": "Invalid Credentials, Access Denied!!"}), 401


# @app.route('/app_get_universities', methods=['GET'])
# def app_get_university():
#     fetch_mongodb_uni_details()
#     return jsonify(uni_dict), 200


# @app.route('/app_view_university', methods=['GET'])
# def app_view_university():
#     data = request.json
#     uni_choice = data['uni_choice']
#     fetch_mongodb_uni_details()

#     for uni, uni_details in uni_dict.items():
#         if uni_choice == uni:
#             return jsonify(uni_details)
#         else:
#             return jsonify({"message": "University not found"}), 400


# @socket.on('connect')
# def socket_on_connect():
#     request_token = request.args.get('token')

#     if request_token:
#         decoded_token = decode_token(request_token)
#         user_id = decoded_token['identity']
#         room = join_room(user_id)

#         redis.set(user_id, room)
#     else:
#         print({"message": "Invalid access"})


# @socket.on("message")
# def handle_message(msg):
#     message = msg['msg']
#     room = msg['room']
#     request_token = request.args.get('token')
#     if request_token:
#         decoded_token = decode_token(request_token)
#         user_name = decoded_token['identity']
#         validate_room = redis.get(room)
#         validate_user = redis.get(user_name)
#         if validate_user:
#             if validate_room:
#                 emit(message, to=room)
#             else:
#                 print({"message": "room not found"})
#         else:
#             print({"message": "Invalid user"})

#     else:
#         print({"message": "Invalid  access"})


# @socket.on("leave_room")
# def leave_room(ur):
#     user_room = ur['ur']
#     fetch_mongodb_user_details()

#     if user_room in user_dict:
#         print({"message": "Can't delete user chat"})
#     else:
#         leave_room(user_room)
#         print({"message": "successfully deleted user chat"})


# if __name__ == "__main__":
#     socket.run(app, debug=True, host="0.0.0.0", allow_unsafe_werkzeug=True)

