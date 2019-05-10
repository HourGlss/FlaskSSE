from flask import Flask, render_template, session, request
from flask_sse import sse
import threading
import queue
import pickle
import base64
import hashlib
import time
app = Flask(__name__)
SESSION_TYPE = "redis"
app.config["REDIS_URL"] = "redis://localhost"
app.secret_key = "sdjhfjkasdhrs8a9r89s7ruwehr"
app.config.from_object(__name__)
app.register_blueprint(sse, url_prefix='/stream')

messages = []


requests = 0

def setid():
    with app.app_context():
        if "id" not in session:
            m = hashlib.sha256()
            m.update(str(time.time()).encode())
            session['id'] = m.hexdigest()
        q.put(session)

@app.route('/')
def index():
    setid()
    return render_template("index.html")

@app.route('/hello')
def publish_hello():
    global requests
    global messages
    setid()
    message = "Hello" + str(requests)
    # sse.publish({"message": message}, type='greeting')
    messages.append(message)
    requests += 1
    return "Message Queued!"

@app.route('/admin')
def admin():
    setid()
    if "permission" in session:
        if session['permission'] >= 2:
            return "Admin!"

    return "Not Admin"

@app.route('/goodbye')
def publish_goodbye():
    global requests
    global messages
    setid()
    message = "Goodbye" + str(requests)
    messages.append(message)
    # sse.publish({"message": message}, type='greeting')
    requests += 1
    return "Message Queued!"

@app.route('/lots')
def publish_lots():
    global requests
    global messages

    setid()
    for i in range(1000):
        message = "lots" + str(requests)
        # sse.publish({"message": message}, type='greeting')
        messages.append(message)
        requests += 1
    return "Messages queued!"

users = {
    "user":("0",0),
    "msct":("1",1),
    "admin":("2",2)
         }
@app.route('/logout', methods=["GET"])
def logout():
    global users
    keys = list(session.keys())
    for k in keys:
        session.pop(k)
    q.put(session)
    return "Session Erased"


@app.route('/login', methods=["GET","POST"])
def login():
    global users
    global q
    print("login called")
    try:
        requested_user = str(request.args['user'])
        password_used = str(request.args['password'])
    except:
        print("login bad")
        return "Malformed Login"
    if "user" in request.args.keys() and "password" in request.args.keys():
        if requested_user in users:
            if  password_used == users[requested_user][0]:
                session['user'] = requested_user
                session['permission'] = users[requested_user][1]
                q.put(session)
                print("login good")
                return "Permission set to {}".format(users[requested_user][1])
            else:
                print("login bad")
                return "Bad password"
        else:
            print("login bad")
            return "User not found"
    else:
        print("login bad")
        return "Login Missing Data"



def send(q):
    global messages
    thread_session = None
    while True:
            time.sleep(3)
            with app.app_context():
                with app.test_request_context():
                    if thread_session is not None:
                        print(thread_session)
                        if "permission" in thread_session:
                            sse.publish({"heartbeat": round(time.time())}, type='heartbeat')
                        if len(messages) > 0:
                            if "permission" in thread_session:
                                if thread_session["permission"] >=1:
                                    messages_to_send = messages
                                    sse.publish({"messages": messages_to_send}, type='message')
                                    messages = []

                    if not q.empty():
                        thread_session = q.get()


with app.app_context():
    q = queue.Queue()
    t = threading.Thread(target=send,args=(q,))
    t.start()