# pylint: disable=no-name-in-module
""" NOTIFICATION """
import json
import syslog
import requests
from configparser import ConfigParser

from flask import request
from library.common import Common
from flask_socketio import SocketIO, emit
from library.postgresql_queries import PostgreSQL
from library.config_parser import config_section_parser

try:

    from __main__ import SOCKETIO

except ImportError:

    from app import SOCKETIO

common = Common()
postgres = PostgreSQL()

@SOCKETIO.on('course_update')
def course_update(json_data):
    """ Message """

    data = {}
    clients = []
    clients.append(request.sid)
    config = ConfigParser()
    config.read("config/config.cfg")
    api_protocol = config_section_parser(config, "APIURL")['protocol']
    api_url = config_section_parser(config, "APIURL")['url']

    if 'token' in json_data.keys() and 'userid' in json_data.keys():

        # GET DATA
        token = json_data['token']
        userid = json_data['userid']

        # CHECK TOKEN
        token_validation = common.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'
            emit('course_update', data, room=clients[0])

        if json_data['type'] == 'course_update':

            if json_data['data']:

                # BASE_URL = "http://localhost:8080/upload/io-course-uploader"
                # BASE_URL = "https://api.olo.mathematischinstituut.nl/upload/io-course-uploader"
                BASE_URL = str(api_protocol) + "://" + str(api_url) + "/upload/io-course-uploader"

                headers = {
                    "accept": "application/json",
                    "token": token,
                    "userid": userid
                }

                response = requests.post(BASE_URL, headers=headers, data=json.dumps(json_data['data']))

    else:

        response = {}
        response['status'] = 'Failed'
        response['alert'] = 'Invalid data!'
        emit('my response', response, room=clients[0])
