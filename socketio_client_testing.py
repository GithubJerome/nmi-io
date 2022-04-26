""" CLIENT SOCKET IO """
from socketIO_client import SocketIO, LoggingNamespace

SOCKETIO = SocketIO('0.0.0.0', 5000, LoggingNamespace)

DATA = {}
DATA['token'] = '192d3215085c43a7ada1151c6d85d48d'
DATA['userid'] = '179b9ee457ae452a916b03a1c8354402'

SOCKETIO.emit('auth', DATA)
