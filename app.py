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
import pandas as pd
import math

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
    query = 'select households."HSHD_NUM", transactions."BASKET_NUM", transactions."PURCHASE", transactions."PRODUCT_NUM", products."DEPARTMENT", products."COMMODITY" from households join transactions on transactions."HSHD_NUM" = households."HSHD_NUM" join products on products."PRODUCT_NUM" = transactions."PRODUCT_NUM" order by "BASKET_NUM" asc;'
    val = ()
    if value: 
        query = 'select households."HSHD_NUM", transactions."BASKET_NUM", transactions."PURCHASE", transactions."PRODUCT_NUM", products."DEPARTMENT", products."COMMODITY" from households join transactions on transactions."HSHD_NUM" = households."HSHD_NUM" join products on products."PRODUCT_NUM" = transactions."PRODUCT_NUM" where (households."HSHD_NUM" = %s) order by "BASKET_NUM" asc;'
        val = (value,)
    db_connect = get_db_connection(query, val)
    if db_connect: 
        return jsonify({"result": db_connect}), 200
    return jsonify({"error": "no data available"}), 400, {'Content-Type': 'application/json; charset=utf-8'}


@app.route('/chartincome', methods=['GET'])
def get_chartincome():
    query = 'select households."INCOME_RANGE", COUNT(*) from households join transactions on transactions."HSHD_NUM" = households."HSHD_NUM" join products on products."PRODUCT_NUM" = transactions."PRODUCT_NUM" GROUP BY households."INCOME_RANGE";'

    db_connect = get_db_connection(query)
    if db_connect: 
        return jsonify({"result": db_connect}), 200
    return jsonify({"error": "no data available"}), 400, {'Content-Type': 'application/json; charset=utf-8'}

@app.route('/chartage', methods=['GET'])
def get_chartage():
    query = 'select households."AGE_RANGE", COUNT(*) from households join transactions on transactions."HSHD_NUM" = households."HSHD_NUM" join products on products."PRODUCT_NUM" = transactions."PRODUCT_NUM" GROUP BY households."AGE_RANGE";'

    total_query = 'select COUNT(*) from households join transactions on transactions."HSHD_NUM" = households."HSHD_NUM" join products on products."PRODUCT_NUM" = transactions."PRODUCT_NUM";'

    db_connect = get_db_connection(query)
    db_total = get_db_connection(total_query)
    result = []
    if db_connect and db_total: 
        total_count = db_total[0]['count']
        for val in db_connect:
            percentage = val['count'] / total_count * 100
            result.append({'AGE_RANGE': val['AGE_RANGE'], 'percentage': math.ceil(percentage*100)/100})
            

        return jsonify({"result": result}), 200
    return jsonify({"error": "no data available"}), 400, {'Content-Type': 'application/json; charset=utf-8'}

@app.route('/charthomeowner', methods=['GET'])
def get_charthomeowner():
    query = 'select households."HOMEOWNER", products."DEPARTMENT", COUNT(households."HOMEOWNER") from households join transactions on transactions."HSHD_NUM" = households."HSHD_NUM" join products on products."PRODUCT_NUM" = transactions."PRODUCT_NUM" GROUP BY products."DEPARTMENT", households."HOMEOWNER";'

    # total_query = 'select COUNT(*) from households join transactions on transactions."HSHD_NUM" = households."HSHD_NUM" join products on products."PRODUCT_NUM" = transactions."PRODUCT_NUM";'

    db_connect = get_db_connection(query)
    # db_total = get_db_connection(total_query)
    result = []
    if db_connect: 
        # total_count = db_total[0]['count']
        # for val in db_connect:
        #     percentage = val['count'] / total_count * 100
        #     result.append({'AGE_RANGE': val['AGE_RANGE'], 'percentage': math.ceil(percentage*100)/100})
        return jsonify({"result": db_connect}), 200
    return jsonify({"error": "no data available"}), 400, {'Content-Type': 'application/json; charset=utf-8'}


@app.route('/uploader/<string:file_for>', methods = ['GET', 'POST'])
def upload_file(file_for):
   if request.method == 'POST':    
        if 'file' not in request.files:
            return ({"error": "No file in request"}), 400
        file = request.files['file']

        if file.filename == '':
            return ({"error": "No filename"}), 400
        
        query = ''
        columns = []
        if file_for == 'products':
            query = 'INSERT INTO products ("PRODUCT_NUM", "DEPARTMENT","COMMODITY", "BRAND_TY", "NATURAL_ORGANIC_FLAG") VALUES (%s, %s, %s, %s, %s);'
            col_names = ['PRODUCT_NUM','DEPARTMENT','COMMODITY', 'BRAND_TY', 'NATURAL_ORGANIC_FLAG']
        elif file_for == 'households':
            query = 'INSERT INTO households ("HSHD_NUM", "L","AGE_RANGE", "MARITAL", "INCOME_RANGE", "HOMEOWNER", "HSHD_COMPOSITION", "HH_SIZE", "CHILDREN") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);'
            col_names = ['HSHD_NUM','L','AGE_RANGE', 'MARITAL', 'INCOME_RANGE', 'HOMEOWNER', 'HSHD_COMPOSITION', 'HH_SIZE', 'CHILDREN']
        elif file_for == 'transactions':
            query = 'INSERT INTO transactions ("BASKET_NUM", "HSHD_NUM","PURCHASE", "PRODUCT_NUM", "SPEND", "UNITS", "STORE_R", "WEEK_NUM", "YEAR") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);'
            col_names = ['BASKET_NUM', 'HSHD_NUM','PURCHASE_', 'PRODUCT_NUM', 'SPEND', 'UNITS', 'STORE_R', 'WEEK_NUM', 'YEAR']
           
        if file: 
            csvData = pd.read_csv(file,names=col_names, header=0)
            for i,row in csvData.iterrows():
                value = ()
                for val in col_names:
                    update_value = row[val]
                    value = value + (update_value,)
                post_db_connection(query, value)
        
        return ({"message": "upload success"}), 200



# app.run()

if __name__ == "__main__":
    server = wsgiserver.WSGIServer(app, host='127.0.0.1',port=6000, debug=True)
    server.start()


