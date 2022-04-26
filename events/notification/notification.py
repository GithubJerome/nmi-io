# pylint: disable=no-name-in-module
""" NOTIFICATION """
import json

from flask import request
from library.common import Common
from flask_socketio import SocketIO, emit
from library.postgresql_queries import PostgreSQL

try:

    from __main__ import SOCKETIO

except ImportError:

    from app import SOCKETIO

common = Common()
postgres = PostgreSQL()

@SOCKETIO.on('notification')
def notification(json_data):
    """ Message """

    data = {}
    clients = []
    clients.append(request.sid)

    if 'token' in json_data.keys() and 'userid' in json_data.keys():

        # GET DATA
        token = json_data['token']
        userid = json_data['userid']

        # CHECK TOKEN
        token_validation = common.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'
            emit('notification', data, room=clients[0])

        if json_data['type'] == 'notification':

            if json_data['data']:

                sql_str = "SELECT * FROM online_user WHERE"
                sql_str += " type='notification' AND"
                sql_str += " account_id='{0}'".format(json_data['data']['account_id'])
                sql_str += " AND status=True"
                response = postgres.query_fetch_all(sql_str)

                if response:
                    for res in response:
                        message = {}
                        message['status'] = 'ok'
                        message['message'] = json_data['data']['description']
                        message['api'] = '/notification'
                        message['notification_id'] = json_data['notification_id']
                        message['notification_type'] = json_data['notification_type']

                        emit('notification', message, room=res['socket_id'])

    else:

        response = {}
        response['status'] = 'Failed'
        response['alert'] = 'Invalid data!'
        emit('my response', response, room=clients[0])
