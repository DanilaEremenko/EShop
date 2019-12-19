import argparse
import colorama
import re
from datetime import datetime
import hashlib
import os
import socket
from threading import Thread
from pandas import DataFrame

from lib.CommonConstants import BUFFER_SIZE
from lib import PacketProcessor

# ---------------------------- COLORS -----------------------------------
COLOR_DATE = colorama.Fore.YELLOW
COLOR_NAME = colorama.Fore.BLUE
COLOR_TEXT = colorama.Fore.WHITE
COLOR_DEBUG = colorama.Fore.RED
COLOR_SERVER_NAME = colorama.Fore.GREEN
COLOR_TOPIC_NAME = colorama.Fore.CYAN
COLOR_DIV_LINES = colorama.Fore.MAGENTA
COLOR_COMMAND = colorama.Fore.GREEN
COLOR_INDEX = colorama.Fore.WHITE

# ---------------------------- HELP -----------------------------------
HELP_CLIENT = "%s------- AVAILABLE CLIENT COMMANDS --------------\n" \
              "%s/add name:str price:str count:int\n" \
              "/buy id:int count:int\n" \
              "/get_products\n" \
              "/fill_up num:int\n" \
              "/help\n" \
              "/exit\n" \
              "%s------------------------------------------------\n%s" % \
              (COLOR_DIV_LINES, COLOR_COMMAND, COLOR_DIV_LINES, colorama.Fore.RESET)


# ------------------------ PRINTS --------------------------
def debug_print(text):
    print("%sDEBUG:%s%s" % (COLOR_DEBUG, text, colorama.Fore.RESET))


def server_msg_print(date, text, end="\n"):
    print("\r%s[%s]:%sSERVER:%s%s " % (COLOR_DATE, date, COLOR_SERVER_NAME, COLOR_TEXT, text), end=end)


def help_print():
    print(HELP_CLIENT)


def print_products(data_dict: dict):
    print("%s------------------ PRODUCTS FROM SERVER --------------- %s" % (COLOR_DIV_LINES, colorama.Fore.RESET))
    print(DataFrame(data_dict))


# ------------------------ WRITE --------------------------------
def write_loop(s, connected, name):
    while connected:
        command = input()
        splited_text = re.sub(" +", " ", command).split(" ")

        if splited_text[0].lower() == "/add" and len(splited_text) == 4:
            try:
                name = splited_text[1]
                price = int(splited_text[2])
                count = int(splited_text[3])
                send_packet = PacketProcessor.get_add_product_packet(name=name, price=price, count=count)
                s.send(send_packet)
                debug_print("ADD PACKET SENDING (OP = %d)" %
                            PacketProcessor.parse_packet(send_packet)[0])

            except:
                debug_print("bad data in /add command")

        elif splited_text[0].lower() == "/buy" and len(splited_text) == 3:
            try:
                id = int(splited_text[1])
                count = int(splited_text[2])
                send_packet = PacketProcessor.get_buy_product_packet(id=id, count=count)
                s.send(send_packet)
                debug_print("BUY PACKET SENDING (OP = %d)" %
                            PacketProcessor.parse_packet(send_packet)[0])
            except:
                debug_print("bad data in /buy command")

        elif splited_text[0].lower() == '/get_products':
            send_packet = PacketProcessor.get_req_prodcuts_packet()
            s.send(send_packet)
            debug_print("REQ_PRODUCTS PACKET SENDING (OP = %d)" %
                        PacketProcessor.parse_packet(send_packet)[0])

        elif splited_text[0].lower() == "/fill_up" and len(splited_text) == 2:
            try:
                num = int(splited_text[1])
                send_packet = PacketProcessor.get_fill_up_ba_packet(num)
                s.send(send_packet)
                debug_print("BUY PACKET SENDING (OP = %d)" %
                            PacketProcessor.parse_packet(send_packet)[0])
            except:
                debug_print("bad data in /fill_up command")

        elif splited_text[0].lower() == '/help':
            help_print()

        elif splited_text[0].lower() == '/exit':
            send_packet = PacketProcessor.get_disc_packet("exit command on client")
            s.send(send_packet)
            connected = False
            debug_print("EXIT PACKET SENDING (OP = %d)" %
                        PacketProcessor.parse_packet(send_packet)[0])
        else:
            debug_print("Undefined command")

    debug_print("\rDISCONNECTION IN WRITE LOOP")
    os._exit(0)


# ------------------------- READ -------------------------------
def read_loop(s, connected):
    while connected:
        opcode, data = PacketProcessor.parse_packet(s.recv(BUFFER_SIZE))

        if opcode == PacketProcessor.OP_SERVER_MSG:
            server_msg_print(text=data["data"]["text"], date=data["data"]["date"])

        elif opcode == PacketProcessor.OP_ANSW_PRODCUTS:
            print_products(data_dict=data["data"])

        elif opcode == PacketProcessor.OP_DISC:
            debug_print("RECEIVED OP_DISC FROM SERVER(%s)" % data["data"]["reason"])
            connected = False
            continue

        else:
            raise Exception("Undefined opcode = %d" % opcode)

    debug_print("\rDISCONNECTION IN READ LOOP")
    os._exit(0)


def registration(s):
    while True:
        name = input("Print your name: ")
        password = input("Print your password: ")
        m = hashlib.md5()
        m.update(name.encode())
        m.update(password.encode())
        client_hash = m.hexdigest()

        send_packet = PacketProcessor.get_registration_packet(name=name, client_hash=client_hash)
        s.send(send_packet)

        opcode, data = PacketProcessor.parse_packet(s.recv(BUFFER_SIZE))

        if opcode == PacketProcessor.OP_REGISTRATION:
            return name
        elif opcode == PacketProcessor.OP_SERVER_MSG:
            server_msg_print(date=data["data"]["date"], text=data["data"]["text"])


# ----------------------------------------------------------------
def main():
    # ---------------- parsing arguments --------------------------
    parser = argparse.ArgumentParser(description="Client for EShop")

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
    s.connect((TCP_IP, TCP_PORT))

    name = registration(s)

    help_print()

    connected = True
    # using threads
    read_thread = Thread(target=read_loop, args=(s, connected), daemon=True)
    write_thread = Thread(target=write_loop, args=(s, connected, name), daemon=True)

    read_thread.start()
    write_thread.start()

    read_thread.join()
    write_thread.join()


if __name__ == '__main__':
    main()
