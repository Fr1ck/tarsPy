#!/usr/bin/env python

import socket

clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = ("127.0.0.1", 8888)

try:
    clientsocket.connect(server_address)
    print("connect successful")
except socket.error:
    print("fail to connect")
    quit()

while True:
    data = input('please input: ')
    clientsocket.send(data.encode())
    server_data = clientsocket.recv(1024).decode()

    print('receive from server：', server_data)

clientsocket.close()
