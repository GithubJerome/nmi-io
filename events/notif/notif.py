# pylint: disable=no-name-in-module
""" NOTIF """
import time

from flask import request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from flask_socketio import SocketIO, emit
# from library.utils import Utils

try:

    from __main__ import SOCKETIO

except ImportError:

    from app import SOCKETIO

# utils = Utils()
postgres = PostgreSQL()
common = Common()
sha_security = ShaSecurity()

@SOCKETIO.on('notif')
def notif(json_data):
    """ NOTIFICATION """

    print("NOTIFICATION")
    data = {}
    clients = []
    clients.append(request.sid)

    if 'token' in json_data.keys() and 'userid' in json_data.keys():

        # GET DATA
        token = json_data['token']
        userid = json_data['userid']
        subscription_type = json_data['type']

        # CHECK TOKEN
        token_validation = common.validate_token(token, userid, request)
        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'
            emit('notification', data, room=clients[0])
            return 0

        temp = {}
        temp['online_user_id'] = sha_security.generate_token(False)
        temp['account_id'] = userid
        temp['token'] = token
        temp['socket_id'] = clients[0]
        temp['type'] = subscription_type
        temp['status'] = True
        temp['created_on'] = time.time()

        postgres.insert('online_user', temp)

        data['message'] = 'Connected!'
        data['status'] = 'ok'
        emit('notification', data, room=clients[0])
        return 1

    else:

        response = {}
        response['status'] = 'Failed'
        response['alert'] = 'Invalid data!'
        emit('notification', response, room=clients[0])
