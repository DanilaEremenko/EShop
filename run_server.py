import argparse

import colorama
from datetime import datetime
import os
import re
import socket
from threading import Thread

from lib.CommonConstants import BUFFER_SIZE
from lib import PacketProcessor
from lib.ForumClasses import DataContainer, Client

# ------------------------------ COLORS -----------------------------------
COLOR_DATE = colorama.Fore.YELLOW
COLOR_NAME = colorama.Fore.BLUE
COLOR_TEXT = colorama.Fore.WHITE
COLOR_DEBUG = colorama.Fore.RED
COLOR_SERVER_NAME = colorama.Fore.RED
COLOR_TOPIC_NAME = colorama.Fore.CYAN
COLOR_DIV_LINES = colorama.Fore.MAGENTA
COLOR_COMMAND = colorama.Fore.GREEN
COLOR_INDEX = colorama.Fore.WHITE

# ---------------------------- CMD -----------------------------------
HELP_SERVER = "%s------------ AVAILABLE SERVER COMMANDS ----------\n" \
              "%s" \
              "exit\n" \
              "%s-------------------------------------------------\n%s" % (
                  COLOR_DIV_LINES, COLOR_COMMAND, COLOR_DIV_LINES, colorama.Fore.RESET)


def debug_print(text):
    print("%sDEBUG:%s" % (colorama.Fore.RED, text))


# ---------------------------------- CMD INPUT  ----------------------------------------------
def cmd_processing(dc: DataContainer):
    while True:
        command = re.sub(" +", " ", input())
        command_splited = command.split()
        if command == "exit":
            exit_server(dc)
        else:
            print("Undefined command = %s. Use help for information" % command)


def client_registration(dc, client):
    opcode, data = PacketProcessor.parse_packet(client.conn.recv(BUFFER_SIZE))
    if opcode == PacketProcessor.OP_REGISTRATION:
        client.name = data["data"]["name"]
        client.is_connected = True
        print("New client = %s(%d) accepted" % (client.name, client.conn.fileno()))


    else:
        print("opcode = %d (%d awaiting)" % (opcode, PacketProcessor.OP_REGISTRATION))
        send_packet = PacketProcessor.get_disc_packet("NO NAME MESSAGE SENDED")
        client.conn.send(send_packet)
        dc.remove_client(reason="BAD OPCODE OF INIT MESSAGE", client=client)
        client.is_connected = False


# ---------------------------- client_processing -----------------------------------
def client_processing(client: Client, dc: DataContainer):
    client_registration(dc, client)

    # -------------------- process client loop -----------------------------------
    while client.is_connected:
        opcode, data = PacketProcessor.parse_packet(client.conn.recv(BUFFER_SIZE))
        send_packet = PacketProcessor.get_disc_packet("BAD OPCODE")
        if opcode == PacketProcessor.OP_ADD_PRODUCT:
            # TODO
            debug_print("OP_ADD_PRODUCT isn't processed")
        elif opcode == PacketProcessor.OP_BUY_PRODUCT:
            # TODO
            debug_print("OP_BUY_PRODUCT isn't processed")
        elif opcode == PacketProcessor.OP_REQ_PRODUCTS:
            # TODO
            debug_print("OP_REQ_PRODUCTS isn't processed")
        elif opcode == PacketProcessor.OP_FILL_UP_BA:
            # TODO
            debug_print("OP_FILL_UP_BA isn't processed")
        elif opcode == PacketProcessor.OP_DISC:
            # TODO
            debug_print("OP_DISC isn't processed")
        else:
            raise Exception("Undefined opcode = %d" % opcode)

        client.conn.send(send_packet)

    print("DISCONNECTED:Client = %s" % client.name)


# ---------------------------------- EXIT----------------------------------
def exit_server(dc: DataContainer):
    dc.remove_all_clients()
    print("SERVER EXITING")
    os._exit(0)


# ---------------------------------- MAIN ----------------------------------
def main():
    dc = DataContainer()
    dc.mock_data()
    # ---------------- parsing arguments --------------------------
    parser = argparse.ArgumentParser(description="Client for SimpleForum")

    parser.add_argument("-i", "--ip", type=str, action='store',
                        help="direcotry with data")

    parser.add_argument("-p", "--port", type=int, action='store',
                        help="port")

    args = parser.parse_args()

    TCP_IP = args.ip
    TCP_PORT = args.port

    if TCP_IP is None:
        raise Exception("-i ip of server was't passed")
    if TCP_PORT is None:
        raise Exception("-p port was't passed ")

    # ---------------- configuration --------------------------
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((TCP_IP, TCP_PORT))
    s.listen(1)

    # running cmd thread
    cmd_thread = Thread(target=cmd_processing, args=(dc,), daemon=True)
    cmd_thread.start()

    while True:
        # new clients accepting
        conn, addr = s.accept()
        new_client = Client(conn=conn, addr=addr, name="not initialized", thread=None, bank_account=0)
        new_client.thread = Thread(target=client_processing,
                                   args=(new_client, dc),
                                   daemon=True)
        dc.mutex.acquire()
        dc.client_list.append(new_client)
        dc.mutex.release()
        new_client.thread.start()


if __name__ == '__main__':
    main()
