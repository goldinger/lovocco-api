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


@app.route("/<string:collection>/<string:index>", methods=['GET', 'PUT'])
def user(collection, index):
    if request.method == 'GET':
        db = get_db()
        return add_headers(jsonify(db[collection].find_one({'_id': ObjectId(index)})))
    elif request.method == 'PUT':
        db = get_db()
        result = db[collection].update_one({'_id': ObjectId(index)}, {"$set": request.get_json(force=True)}, upsert=False)
        return add_headers(jsonify({'status': 'OK', 'count': result.modified_count}))


def add_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route("/<string:collection>", methods=['POST', 'GET', 'PUT'])
def insert_user(collection):
    if request.method == 'POST':
        db = get_db()
        body = request.get_json(force=True)
        result = db[collection].insert_one(body)
        return add_headers(jsonify({'_id': result.inserted_id, 'status': 'OK'}))
    if request.method == 'PUT':
        db = get_db()
        body = request.get_json(force=True)
        result = db[collection].insert_one(body)
        return add_headers(jsonify({'_id': result.inserted_id, 'status': 'OK'}))
    if request.method == 'GET':
        db = get_db()
        args = dict(request.args)
        results = db[collection].find(args)
        response = jsonify(list(results))
        return add_headers(response)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
