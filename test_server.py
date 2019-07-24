# -*- coding:utf-8 -*-

import select
import socket
import queue
import struct

# 存放句柄和socket的字典
fd_to_socket = {}
# 存放socket和信息的字典
message_queues = {}

# 建立serve端接收请求用的socket
domain = socket.AF_INET
socket_type = socket.SOCK_STREAM
_sock = socket.socket(domain, socket_type)

epoll = select.epoll()


class NetThread:

    def __init__(self):
        pass
        # 建立用于通知和关闭的socket
        # _shutdown_sock = socket(domain, socket_type)
        # _notify_sock = socket(domain, socket_type)
        #
        # if not _shutdown_sock:
        #     print("_shutdown_sock  invalid")
        #
        # if not _notify_sock:
        #     print("_notify_sock invalid")

    def bind(self, ip, port):

        if not _sock:
            print("bind_sock invalid")

        # 设置ip端口复用
        _sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server_address = (ip, port)
        try:
            # 绑定ip地址
            _sock.bind(server_address)
        except socket.error:
            print("bind error")
        else:
            print("server already bind fd is ", _sock)

        connection_backlog = 1024
        try:
            _sock.listen(connection_backlog)
        except socket.error:
            print("listen error")

        try:
            _sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        except socket.error:
            print("set keepAlive error")

        try:
            _sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except socket.error:
            print("set TcpNoDelay error")

        try:
            _sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
        except socket.error:
            print("set closeWait error")

        try:
            _sock.setblocking(False)
        except socket.error:
            print("set unblock error")

        return _sock

    def create_epoll(self):

        # epoll.register(self._shutdown_sock.fileno(), select.EPOLLIN | select.EPOLLET)
        # epoll.register(self._notify_sock.fileno(), select.EPOLLIN | select.EPOLLET)
        epoll.register(_sock.fileno(), select.EPOLLIN | select.EPOLLET)

    def run(self):

        fd_to_socket[_sock.fileno()] = _sock

        while True:

            timeout = 20
            events = epoll.poll(timeout)

            for fd, event in events:

                ev_socket = fd_to_socket[fd]
                if ev_socket == _sock:
                    print("LISTEN")
                    ret = True
                    while ret:
                        ret = self.net_accept()

                elif event & select.EPOLLHUP:
                    print("EPOLLHUP")
                    self.net_close(fd)

                elif event & select.EPOLLIN:
                    if self.net_in(fd, ev_socket):
                        print("EPOLLIN")

                elif event & select.EPOLLOUT:
                    self.net_out(fd, ev_socket)
                    print("EPOLLOUT")

    def net_accept(self):

        try:
            connection, address = _sock.accept()
            print("server accept successful address is", address)

            # 新连接socket设置为非阻塞
            connection.setblocking(False)

            # 注册新连接fd到待读事件集合
            epoll.register(connection.fileno(), select.EPOLLIN)

            try:
                connection.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            except socket.error:
                print("set connection keepAlive error")

            try:
                connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            except socket.error:
                print("set connection TcpNoDelay error")

            try:
                connection.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
            except socket.error:
                print("set connection closeWait error")

            try:
                connection.setblocking(False)
            except socket.error:
                print("set connection unblock error")

            # 把新连接的文件句柄以及对象保存到字典
            fd_to_socket[connection.fileno()] = connection

            # 以新连接的对象为键值，之后读取时信息保存每个连接的信息
            message_queues[connection] = queue.Queue()

            return True

        except socket.error:
            return False

    def net_close(self, fd):

        epoll.ungregister(fd)
        # 关闭客户端文件句柄的socket
        fd_to_socket[fd].close()
        # 在字典中删除与已关闭客户端相关的信息
        del fd_to_socket[fd]

    def net_in(self, fd, ev_socket):

        data = ev_socket.recv(1024).decode()

        if data:
            print("recv：", data, " from：", ev_socket.getpeername())
            # 将数据放入对应客户端的字典
            message_queues[ev_socket].put(data)
            # 修改读取到消息的连接到等待写事件集合(即对应客户端收到消息后，再将其fd修改并加入写事件集合)
            epoll.modify(fd, select.EPOLLOUT)

            return True
        else:
            return False

    def net_out(self, fd, ev_socket):

        try:
            # 从字典中获取对应客户端的信息
            msg = message_queues[ev_socket].get_nowait()

        except queue.Empty:
            print(ev_socket.getpeername(), " queue empty")
            # 修改文件句柄为读事件
            epoll.modify(fd, select.EPOLLIN)

        else:
            print("send msg：", msg, " to：", ev_socket.getpeername())
            # 发送数据
            ev_socket.send(msg.encode())

    def __del__(self):
        # 在epoll中注销服务端文件句柄
        epoll.unregister(_sock.fileno())
        # 关闭epoll
        epoll.close()
        # 关闭服务器socket
        _sock.close()


if __name__ == '__main__':

    ip = "127.0.0.1"
    port = 8888

    vNetThread = NetThread()
    vNetThread.bind(ip, port)
    vNetThread.create_epoll()
    vNetThread.run()

    del vNetThread






