#Para crear el ambiente virtual
#python3 -m venv .venv
#source .venv/bin/activate

from __future__ import print_function
from geventwebsocket import WebSocketServer, WebSocketApplication, Resource
#python3.7 -m pip install werkzeug
from werkzeug.debug import DebuggedApplication
from flask import Flask, render_template
import json
#python3.7 -m pip install gevent
from gevent import monkey

#db and aiml imports
#python3.7 -m pip install tinydb
from tinydb import TinyDB, Query
import os
#python3.7 -m pip install python-aiml
import aiml

monkey.patch_all()

# Para la interfaz y otras cosas
flask_app = Flask(__name__)
flask_app.debug = True


k = aiml.Kernel()


BRAIN_FILE = "brain.dump"


if os.path.exists(BRAIN_FILE):
    print("Cargando desde archivo cerebral file: " + BRAIN_FILE)
    k.loadBrain(BRAIN_FILE)
else:
    print("Parsing aiml files")
    k.bootstrap(learnFiles="std-startup.aiml", commands="load aiml b")
    print("Cargando Skynet: " + BRAIN_FILE)
    k.saveBrain(BRAIN_FILE)


db = TinyDB('conversations.json')
Usuario = Query()


class ChatApplication(WebSocketApplication):
    
    def on_open(self):
        print("Some client connected!")
    #Si hay un mensaje en la cola hace esto
    def on_message(self, message):
        if message is None:
            return

        message = json.loads(message)

        
        if message['msg_type'] == 'message':
            self.broadcast(message)
        elif message['msg_type'] == 'update_clients':
            self.send_client_list(message)

    
    def send_client_list(self, message):
        current_client = self.ws.handler.active_client
        current_client.nickname = message['nickname']

        
        username = current_client.nickname
        if not len(username)>0:
            username='desconocido'
        user=db.search(Usuario.user == username)
        #print(user)
        
        if len(user) == 0:
            user = db.insert({'user': username, 'conversations': [[]]})
            #user = db.get(eid=user)
        else:
          user=user[0]
          conv=user['conversations']
          if not conv:
            print(conv)
          #conv.append([])
          
          #if not conv:
            
            #db.update({'conversations':conv},doc_ids=[user.doc_id])

        self.ws.send(json.dumps({
            'msg_type': 'update_clients',
            'clients': [
                getattr(client, 'nickname', 'anonymous')
                for client in self.ws.handler.server.clients.values()
            ]
        }))

    def broadcast(self, message):
        nickname = message['nickname']
        message_ = message['message']
        
        user=db.search(Usuario.user == nickname)
        if len(user)==0:
          user=db.insert({'user':username,'conversations':[[]]})
          user=db.get(eid=user)
        else:
          user=user[0]
        ans=k.respond(message_)
        conv=user['conversations']
        conv[-1].append({'msg':message_,'ans':ans})
        db.update({'conversations':conv},doc_ids=[user.doc_id])
        #emit('response', {'data': ans.lower()})
        print(ans)

        for client in self.ws.handler.server.clients.values():
            client.ws.send(json.dumps({
                'msg_type': 'message',
                'nickname': message['nickname'],
                'message': message['message']
            }))
        for client in self.ws.handler.server.clients.values():
            client.ws.send(json.dumps({
                'msg_type': 'botanswer',
                'nickname': 'CHATBOT',
                'message': ans
            }))

    def on_close(self, reason):
        print("Connection closed!")


@flask_app.route('/')
def index():
    return render_template('index.html')
k.respond("load aiml s")

WebSocketServer(
    ('0.0.0.0', 5000),

    Resource([
        ('^/chat', ChatApplication),
        ('^/.*', DebuggedApplication(flask_app))
    ]),

    debug=False
).serve_forever()
