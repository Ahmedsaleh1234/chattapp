from flask import Flask, render_template, url_for, request
from kafka import KafkaConsumer, KafkaProducer
import os
import time
import json
import pymongo

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'any random string'

myclient = pymongo.MongoClient('mongodb://localhost:27017/')
user_db = myclient['authentication']
user_table = user_db['user_info']
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/dash')
def dash():
    return render_template('dashboard.html')

@app.route('/register' ,methods=['GET', 'POST'])
def reg():
    if(request.method == 'POST'):
        req = request.form
        req =dict(req)
        print(req)
        query = user_table.find({'name':req['name']})
        flag = 0
        for i in query:
            if(i['email'] == req['email']):
                flag = 1
                break
        
        reg_dict = {
            'name' : req['name']
            , 'email':req['email']
            , 'password': req['password']
        }
        if(flag == 0):
            temp = user_table.insert_one(reg_dict)
            return render_template('dashboard.html')
        else:
            return 'user already exist'
        

    return render_template('register.html')

@app.route('/sign in', methods=['GET', 'POST'])
def sign():
    if(request.method == 'POST'):
        req =request.form
        req = dict(req)
        print(req)
        query = user_table.find({'email':req['email']})
        flag = 0
        tmp = None
        for x in query:
            if (x['email'] == req['email']):
                flag = 1
                tmp = x
                break
        if (flag == 1):
            if(tmp['password'] == req['password']):
                return render_template('dashboard.html')
            else:
                return 'invalid password or email'
    else:
        return render_template('signin.html')



if __name__ == '__main__':
    app.run(debug=True)