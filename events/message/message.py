# pylint: disable=no-name-in-module
""" MESSAGE """
import json
import syslog
import requests

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

@SOCKETIO.on('message')
def message(json_data):
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
            emit('message', data, room=clients[0])

        if json_data['type'] == 'message':

            if json_data['data']:

                # json_data['data']: {'url': 'user/update'}

                p_status = "json_data['data']: {0}".format(json_data['data'])
                syslog.syslog(p_status)
                # api-endpoint

                BASE_URL = "http://localhost:8080" + json_data['data']['url']
                
                headers = {
                    "accept": "application/json",
                    "token": json_data['data']['token'],
                    "userid": json_data['data']['userid']
                }
                    # "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36"

                response = requests.get(BASE_URL, headers=headers, params=json_data['data']['params'])

    else:

        response = {}
        response['status'] = 'Failed'
        response['alert'] = 'Invalid data!'
        emit('my response', response, room=clients[0])
