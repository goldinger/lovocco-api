import random
import re
import hashlib
from flask import Flask, jsonify, request
import json
from datetime import datetime
from pymongo import MongoClient
import pymongo
from bson.objectid import ObjectId


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return str(o)
        return json.JSONEncoder.default(self, o)


app = Flask(__name__)
app.json_encoder = JSONEncoder


def get_db() -> pymongo.database.Database:
    client = MongoClient(port=27017)
    return client.lovocco


# @app.route("/<string:collection>/<string:index>", methods=['GET', 'PUT'])
# def user(collection, index):
#     if request.method == 'GET':
#         db = get_db()
#         return add_headers(jsonify(db[collection].find_one({'_id': ObjectId(index)})))
#     elif request.method == 'PUT':
#         db = get_db()
#         result = db[collection].update_one({'_id': ObjectId(index)}, {"$set": request.get_json(force=True)}, upsert=False)
#         return add_headers(jsonify({'status': 'OK', 'count': result.modified_count}))


def add_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


# @app.route("/<string:collection>", methods=['POST', 'GET', 'PUT'])
# def insert_user(collection):
#     if request.method == 'POST':
#         db = get_db()
#         body = request.get_json(force=True)
#         result = db[collection].insert_one(body)
#         return add_headers(jsonify({'_id': result.inserted_id, 'status': 'OK'}))
#     if request.method == 'PUT':
#         db = get_db()
#         body = request.get_json(force=True)
#         result = db[collection].insert_one(body)
#         return add_headers(jsonify({'_id': result.inserted_id, 'status': 'OK'}))
#     if request.method == 'GET':
#         db = get_db()
#         args = dict(request.args)
#         results = db[collection].find(args)
#         response = jsonify(list(results))
#         return add_headers(response)


@app.route("/register", methods=['PUT'])
def register():
    if request.method == 'PUT':
        body = dict(request.get_json(force=True))
        email = body.get('email')
        password = body.get('password')
        if not re.match("[^@]+@[^@]+\.[^@]+", email):
            return add_headers(jsonify({"status": "KO", "message": "invalid email format"}))
        if password in ['', None]:
            return add_headers(jsonify({"status": "KO", "message": "invalid password"}))

        email = email.lower()
        db = get_db()
        if db.users.find_one({"email": email}):
            return add_headers(jsonify({"status": "KO", "message": "email already exists"}))
        token = hashlib.sha256((email + password + str(random.randint(1, 9999))).encode('utf-8')).hexdigest()
        result = db.users.insert_one({"email": email, "password": password, "token": token, "createdAt": datetime.now()})
        user_id = result.inserted_id
        db.lovers.insert_one({"userId": user_id, "configured": False})
        return add_headers(jsonify({"status": "OK", "token": token}))


@app.route("/authenticate", methods=['POST'])
def authenticate():
    if request.method == 'POST':
        db = get_db()
        body = dict(request.get_json(force=True))
        email = body.get('email')
        if email is not None:
            email = email.lower()
        password = body.get('password')
        result = db.users.find_one({"email": email, "password": password})
        if result is None:
            return add_headers(jsonify({"status": "KO"}))
        return add_headers(jsonify({"token": result.get('token')}))


@app.route("/myProfile", methods=['GET'])
def my_profile():
    if request.method == 'GET':
        db = get_db()
        args = dict(request.args)
        token = args.get('token')
        if token is None:
            return add_headers(jsonify({"status": 'KO'}))
        user = db.users.find_one({"token": token})
        if user:
            user_id = str(user.get('_id'))
            lover = db.lovers.find_one({'userId': user_id})
            if lover:
                return add_headers(jsonify(lover))
        return add_headers(jsonify({"status": "KO"}))


if __name__ == "__main__":
    app.run(host='0.0.0.0')
