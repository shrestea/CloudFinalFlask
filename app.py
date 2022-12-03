#!/usr/bin/env python
# encoding: utf-8
import os
import json
from flask import Flask, request, jsonify, abort, send_from_directory
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename
import wsgiserver
from init_db import get_db_connection, post_db_connection
import psycopg2.extras

app = Flask(__name__)
cors = CORS(app)
app.config['UPLOAD_FOLDER'] = 'files'
ALLOWED_EXTENSIONS = {'csv'}

@app.route('/', methods=['GET'])
def get_and_return():
    return jsonify({"check":"value"})

@app.route('/user', methods=['GET'])
def query_records():
    name = request.args.get('name')
    print(name)
    with open('data.txt', 'r') as f:
        try:
            contents = f.read()
            print(contents)
            records = json.loads(contents)
        except json.decoder.JSONDecodeError:
            return jsonify({'status': 400, 'error': 'Data not loaded properly'}) 

        for record in records:
            if record['username'] == name:
                return jsonify(record), 200
    return jsonify({status: 400, 'error': 'user does not exist'}), 400

@app.route('/data', methods=['GET'])
def get_data():
    result = get_db_connection('SELECT "HSHD_NUM", "L", "AGE_RANGE", "MARITAL", "INCOME_RANGE" FROM households;')
    print(result)
    # data = []
    # for i in books:
    #     data.append({
    #         'hshd_num': i[0],
    #         'l': i[1],
    #         'age_range': i[2].strip(),
    #         'marital': i[3],
    #         'income_range': i[4]
    #     })
    return jsonify({'result': result})


@app.route('/login-user', methods=['POST'])
def login_user():
    record = json.loads(request.data)
    username = record['username']
    password = record['password']

    is_user_query = 'SELECT username, email FROM users WHERE username = %s AND password = %s;'
    is_user_values = (username, password)
    is_user = get_db_connection(is_user_query, is_user_values)
    
    if len(is_user) > 0:
        response = {"result": is_user[0]}
        # response.headers.add('Access-Control-Allow-Origin', '*')
        return jsonify(response), 200, {'Content-Type': 'application/jsons; charset=utf-8'}

    return jsonify({"error": "username/password does not match"}), 400, {'Content-Type': 'application/json; charset=utf-8'}

@app.route('/register-user', methods=['POST'])
def create_record():
    record = json.loads(request.data)
    username = record['username']
    email = record['email']
    password = record['password']

    is_user_query = 'SELECT "username", "email" FROM users WHERE email = %s OR username = %s;'
    is_user_values = (email, username)
    is_user = get_db_connection(is_user_query, is_user_values)

    if len(is_user) == 0:
        insert_query = "INSERT INTO users (USERNAME, EMAIL, PASSWORD) VALUES (%s, %s, %s)"
        record_to_insert = (username, email, password)
        post_db_connection(insert_query, record_to_insert)
        return jsonify({'username': username, "email": email}), 200
    return jsonify({"error": "user already exists"}), 400, {'Content-Type': 'application/json; charset=utf-8'}

@app.route('/datastore', methods=['GET'])
def get_datastore():
    value = request.args.get('value')
    print(value)
    query = 'select households."HSHD_NUM", transactions."BASKET_NUM", transactions."PURCHASE", transactions."PRODUCT_NUM", products."DEPARTMENT", products."COMMODITY" from households join transactions on transactions."HSHD_NUM" = households."HSHD_NUM" join products on products."PRODUCT_NUM" = transactions."PRODUCT_NUM" where (households."HSHD_NUM" = %s) order by "BASKET_NUM" asc;'
    val = (value,)
    db_connect = get_db_connection(query, val)
    if db_connect: 
        return jsonify({"result": db_connect}), 200
    return jsonify({"error": "no data available"}), 400, {'Content-Type': 'application/json; charset=utf-8'}


@app.route('/chartage', methods=['GET'])
def get_chartage():
    query = 'select households."INCOME_RANGE", COUNT(*) from households join transactions on transactions."HSHD_NUM" = households."HSHD_NUM" join products on products."PRODUCT_NUM" = transactions."PRODUCT_NUM" GROUP BY households."INCOME_RANGE";'

    db_connect = get_db_connection(query)
    if db_connect: 
        return jsonify({"result": db_connect}), 200
    return jsonify({"error": "no data available"}), 400, {'Content-Type': 'application/json; charset=utf-8'}

@app.route('/', methods=['DELETE'])
def delte_record():
    record = json.loads(request.data)
    new_records = []
    with open('data.txt', 'r') as f:
        data = f.read()
        records = json.loads(data)
        for r in records:
            if r['name'] == record['name']:
                continue
            new_records.append(r)
    with open('data.txt', 'w') as f:
        f.write(json.dumps(new_records, indent=2))
    return jsonify(record)

@app.route('/uploader/<string:username>', methods = ['GET', 'POST'])
def upload_file(username):
   if request.method == 'POST':
        # check if the post request has the file part
        print(username)

        if 'file' not in request.files:
            return ({"error": "No file in request"}), 400
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            return ({"error": "No filename"}), 400
        if file:
            new_records = []
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            total_words=0
            with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'r') as fn:
                read_data = fn.read()
                total_words = read_data.split()
            with open('data.txt', 'r') as f:
                data = f.read()
                records = json.loads(data)
            for record in records:
                if record['username'] == username:
                    record['filename'] = filename
                    record['count'] = len(total_words)
                new_records.append(record)
            with open('data.txt', 'w') as f:
                f.write(json.dumps(new_records, indent=2))
            return ({"message": "upload success", "count": len(total_words)}), 200



# app.run()

if __name__ == "__main__":
    server = wsgiserver.WSGIServer(app, host='127.0.0.1',port=5000, debug=True)
    server.start()


