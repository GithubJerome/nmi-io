
""" CONNECTION """

from flask import request
from library.common import Common
from flask_socketio import SocketIO, emit
from library.postgresql_queries import PostgreSQL

try:

    from __main__ import SOCKETIO

except ImportError:

    from app import SOCKETIO

postgres = PostgreSQL()

@SOCKETIO.on('connect')
def connect():
    """ CONNECT """
    # print('connect!')
    emit('my response', {'data': 'Connected'})
    # emit('my response', {'data': 'Connected'})
    # response = {'top_id': "Bot", 'message': "Client " + str(request.sid) + " connected!"}
    # emit('chats', response, broadcast=True)

@SOCKETIO.on('disconnect')
def disconnect():
    """ DISCONNECT """

    conditions = []

    conditions.append({
        "col": "socket_id",
        "con": "=",
        "val": str(request.sid)
        })

    changes = {}
    changes['status'] = False

    postgres.update('online_user', changes, conditions)
