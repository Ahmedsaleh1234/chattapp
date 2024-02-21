from flask import Flask, render_template, url_for, request, redirect
from kafka import KafkaConsumer, KafkaProducer
import os
import time
import json
import pymongo
import datetime
from flask_socketio import SocketIO, send, join_room
"""this a flask module"""
app = Flask(__name__)
app.secret_key = 'any random string'
socketio = SocketIO(app, cors_allowed_origins="*")


myclient = pymongo.MongoClient('mongodb://localhost:27017/')
user_db = myclient['authentication']
user_table = user_db['user_info']
#producer = KafkaProducer(bootstrap_server = 'localhost:9092')
user_data = {}
msg_count = 0
connected_clients = {} 
"""Store connected clients and their chat IDs"""
@app.route('/')
@app.route('/home')
def home():
    """an function to home page"""
   
    return render_template('home.html')

@app.route('/dash/<string:user_id>', methods=['GET', 'POST'])
def dash(user_id):
    """this function deploy the dashboard page"""
    global user_data
    chat_id = user_data[user_id]['cid']
    if chat_id != None:
        chat_id = chat_id.strip()
    if user_id in user_data:
        if chat_id in user_data[user_id]['msg_list']:
            return render_template('dashboard.html',
                                    uid=user_id,
                                    cid=user_data[user_id]['cid'],
                                    user_list=user_data[user_id]['user_list'],
                                    group_list=user_data[user_id]['group_list'],
                                    msg_list=user_data[user_id]['msg_list'][chat_id])
        else:
            return render_template('dashboard.html',
                                    uid=user_id,
                                    cid=user_data[user_id]['cid'],
                                    user_list=user_data[user_id]['user_list'],
                                    group_list=user_data[user_id]['group_list'],
                                    msg_list={})


    return redirect('/home')

@app.route('/register' ,methods=['GET', 'POST'])
def reg():
    """this funcion to deploy an sign up page"""
    global user_data
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
            uid = req['name']
            user_data[uid] = {}
            user_data[uid]['cid'] = None
            user_data[uid]['user_list'] = []
            user_data[uid]['group_list'] = []
            user_data[uid]['msg_list'] = {}
            return redirect('/dash/'+str(uid))
        else:
            error = "user already exist !"
            return render_template('register.html',error=error)
        

    return render_template('register.html')

@app.route('/sign in', methods=['GET', 'POST'])
def sign():
    """this funcion is to check if user is already exict"""
    global user_data
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
                uid = tmp['name']
                user_data[uid] = {}
                user_data[uid]['cid'] = None
                user_data[uid]['user_list'] = []
                user_data[uid]['group_list'] = []
                user_data[uid]['msg_list'] = {}

                return redirect('/dash/' + str(uid))
            else:
                return 'invalid password'
    else:
        return render_template('signin.html')
    if (flag == 0):
        return 'user is not exist'
    

@app.route('/user/<string:user_id>', methods=['GET', 'POST'])
def user(user_id):
    """this function is to read from user file"""
    global user_data
    file = open('users.txt', 'r')
    data = file.readlines()
    user_data[user_id]['user_list'] = data
    return redirect('/dash/'+str(user_id))

@app.route('/group/<string:user_id>', methods=['GET', 'POST'])
def group(user_id):
    """this function is to read from group file"""
    global user_data
    file = open('groups.txt', 'r')
    data = file.readlines()
    user_data[user_id]['group_list']= data
    return redirect('/dash/'+str(user_id))
@app.route('/update_cid/<string:user_id>/<string:chat_id>', methods=['GET', 'POST'])
def update(user_id, chat_id):
    global user_data
    user_data[user_id]['cid'] = chat_id
    return redirect('/dash/'+ str(user_id))


@app.route('/send_msg/<string:user_id>', methods=['GET', 'POST'] )
def send_msg(user_id):
    global user_data, msg_count
    if(request.method == 'POST'):
        req = request.form
        req = dict(req)
        print(req)
        text = req['text']#text text
        chat_id = user_data[user_id]['cid']
        if chat_id != None:
            chat_id = chat_id.strip()
        c = datetime.datetime.now()
        timestamp = c.strftime("%I:%M %p")
        msg_count += 1
       
        """dict_msg = {
            "op_type":"send",
            "uid1":user_id,
            "uid2":chat_id,
            "text":text,
            "timestamp":timestamp,
            "msg_id":msg_count
                    }
        topic = "ActionServer"
        """
       
       # producer.send(topic,json.dumps(dict_msg).encode('utf-8'))
        
        if chat_id in user_data[user_id]['msg_list']:
            user_data[user_id]['msg_list'][chat_id][msg_count] = {}
            user_data[user_id]['msg_list'][chat_id][msg_count]['text'] = text
            user_data[user_id]['msg_list'][chat_id][msg_count]['send_uid'] = user_id
            user_data[user_id]['msg_list'][chat_id][msg_count]['timestamp'] =timestamp
        else:
            user_data[user_id]['msg_list'][chat_id]={} 
            user_data[user_id]['msg_list'][chat_id][msg_count] = {}
            user_data[user_id]['msg_list'][chat_id][msg_count]['text'] = text
            user_data[user_id]['msg_list'][chat_id][msg_count]['send_uid'] = user_id
            user_data[user_id]['msg_list'][chat_id][msg_count]['timestamp'] =timestamp
    return redirect('/dash/'+str(user_id))


@app.route('/logout/<string:user_id>', methods=['GET', 'POST'])
def logout(user_id):
    """this function is to logout the user"""
    global user_data
    print('logout', user_id)
    user_data.pop(user_id)

    
    return redirect('/home')

@app.route('/delete/<string:user_id>', methods=['GET', 'POST'])
def delete(user_id):
    """this function is to delete user"""
    global user_data
    print('logout', user_id)
    user_table.delete_one({'name': user_id})
    return redirect('/home')
@socketio.on("connect")
def connect(auth):
    global user_data
    name = user_data[auth]
    join_room()
    



if __name__ == '__main__':
    socketio.run(app,debug=True)