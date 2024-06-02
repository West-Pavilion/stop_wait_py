"""
    欢迎使用我的停止等待协议模拟器！
    所谓停止等待协议，就是发送方发送一个数据报，如果没有得到接收方
    的确认，就进入等待状态，不发送之后的数据报，除非超时计时器倒计时
    结束，那么就要重新发送之前的数据报。
    本模拟器的特色有：
    1. 基于 socket 模块实现了基本的 C/S 结构的通信
    2. 使用 random 模块模拟了发送方（客户端）丢包的情况
    3. 在上述的丢包情况下，实现了 ARQ（自动重传请求），
    即客户端在其超时计时器时间结束时会自动重新发送丢失的数据报

    作者：李悠然
    作者的学号：2022405532
"""

import socket
import random
from threading import Thread
from time import sleep

ip = '127.0.0.1'
port = 1234

# 丢包率将从配置文件 'lost_packet.ini' 中读取，您可以自行配置
lost_possibility = 0


class server:
    """
        server 类有自己的 ack 和 seq 值
    """
    ack = 2
    seq = 1

    def __init__(self, ip, port) -> None:
        self.is_run = True
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((ip, port))
        self.sock.listen(15)

    def terminate(self):
        self.is_run = False

    def inner_server_start(self):
        conn, addr = self.sock.accept()
        while self.is_run:
            client_message = conn.recv(4096)

            raw_message = client_message.decode()
            raw_message_list = raw_message.split(maxsplit=2)
            message_ack = int(raw_message_list[0])
            message_seq = int(raw_message_list[1])
            message_data = raw_message_list[2]

            if message_data == 'exit':
                self.terminate()
                break

            # 生成一个随机数，这个随机数决定了模拟丢包的结果
            random_num = random.random()
            if random_num < lost_possibility:
                print('丢包了，服务端发送的数据报不正确')
                continue

            print('服务端已经正确收到来自客户端的数据：')
            print('ack 的值为：' + message_ack.__str__())
            print('seq 的值为：' + message_seq.__str__())
            print('数据部分：' + message_data + '\n')

            # 服务端每收到一个数据包，sleep 两秒时间模拟数据的处理，
            # 并将自己的 ack 值设置为客户端发来的数据报中的 seq 值 + 1
            sleep(2)
            server.ack = message_seq + 1

            print('正在向客户端发送确认信息. . . \n')

            pend_to_send_message = server.ack.__str__() + ' ' + server.seq.__str__()
            conn.sendall(pend_to_send_message.encode())

            # 确认信息发送完毕，下一次发送时附带的 seq 信息为本次的值 + 1
            server.seq += 1

    def start_server(self):
        server_thread = Thread(target=self.inner_server_start)
        server_thread.start()


class client:
    """
        client 类也有自己的 ack 和 seq 值
    """
    ack = 1
    seq = 10

    # 这个字段用于保存上一次发送的数据，如果在超时计时器倒计时结束时
    # 还没有收到服务端的确认信息，就重新发送这里缓存的数据
    last_send = ''

    def __init__(self, ip, port) -> None:
        self.is_run = True
        self.sock = socket.socket()

        # 设置超时计时器的等待时长为 3 秒
        self.sock.settimeout(3)

        self.sock.connect((ip, port))

    def terminate(self):
        self.is_run = False

    def start_client(self):
        while self.is_run:
            if client.seq != 10:
                try:
                    server_message = self.sock.recv(4096)
                except:
                    print('\n超时计时器的倒计时已经结束，即将超时重传. . . \n')
                    print('上一次发送的数据是：' + client.last_send)
                    sleep(2)
                    self.sock.sendall(client.last_send.encode())
                    continue

                raw_message = server_message.decode()
                raw_message_list = raw_message.split()
                message_ack = int(raw_message_list[0])
                message_seq = int(raw_message_list[1])

                print('客户端已经正确收到来自服务端的数据：')
                print('ack 的值为：' + message_ack.__str__())
                print('seq 的值为：' + message_seq.__str__() + '\n')

                # 将 client 的 ack 值设置为服务器端发来的数据报的 seq 值 + 1
                client.ack = message_seq + 1

            pend_to_send_message = input('请输入需要发送的数据吧：')
            decorated_message = client.ack.__str__() + ' ' + client.seq.__str__() + \
                ' ' + pend_to_send_message
            self.sock.sendall(decorated_message.encode())
            client.last_send = decorated_message

            # 如果用户输入的是 exit，那么先将该信息发送给服务端（代码在上面），
            # 再退出客户端程序（这部分代码在下面）
            if pend_to_send_message == 'exit':
                self.terminate()
                print('正在退出程序. . . ')
                break

            # 客户端数据发送完毕，下一次发送的 seq 值为本次的值 + 1
            client.seq += 1


def read_config():
    with open('lost_packet.ini') as file:
        global lost_possibility
        print('正在从 lost_packet.ini 配置文件中读取丢包概率. . . ')
        data = file.readline().split()
        lost_possibility = float(data[2])


def main():
    print('欢迎使用停等协议模拟器！\n')
    print('用法：输入要发送的数据，本程序将自动将其发送至服务端，')
    print('给出服务器收到的数据报中的 ack 和 seq 值，并显示客户端收到的确认消息')
    print('当使用完毕后，可以输入 exit 以退出本模拟器\n')
    read_config()
    print('当前丢包率为：' + str(lost_possibility) + '\n')
    server_instance = server(ip, port)
    client_instance = client(ip, port)
    server_instance.start_server()
    client_instance.start_client()


if __name__ == '__main__':
    main()
