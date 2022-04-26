# pylint: disable=wrong-import-position, import-error, unused-import
""" APP """
from flask import request
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from library.postgresql_queries import PostgreSQL

# https://flask-socketio.readthedocs.io/en/latest/
# https://github.com/socketio/socket.io-client

APP = Flask(__name__, template_folder='ui')
CORS(APP)
POSTGRES = PostgreSQL()

SOCKETIO = SocketIO(APP, cors_allowed_origins="*")

# CONNECTION EVENTS
from events.connection import connection

# AUTH EVENTS
from events.auth import auth

# NOTIFICATION EVENTS
from events.notification import notification

# UPDATE COURSE EVENTS
from events.course_update import course_update

# USER NOTIFICATION EVENTS
from events.notif import notif

# MESSAGE EVENTS
from events.message import message

@APP.route('/')
def home():
    """ HTML """
    return render_template('nmi-socket-io.html')

SQL_STR = "UPDATE online_user SET status=False"

POSTGRES.exec_query(SQL_STR)

if __name__ == '__main__':
    SOCKETIO.run(APP, host='0.0.0.0', port=5001)
