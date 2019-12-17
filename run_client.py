import argparse
import colorama
from datetime import datetime
import os
import re
import socket
from threading import Thread

from lib.CommonConstants import BUFFER_SIZE
from lib import PacketProcessor

# ---------------------------- COLORS -----------------------------------
COLOR_DATE = colorama.Fore.YELLOW
COLOR_NAME = colorama.Fore.BLUE
COLOR_TEXT = colorama.Fore.WHITE
COLOR_DEBUG = colorama.Fore.RED
COLOR_SERVER_NAME = colorama.Fore.RED
COLOR_TOPIC_NAME = colorama.Fore.CYAN
COLOR_DIV_LINES = colorama.Fore.MAGENTA
COLOR_COMMAND = colorama.Fore.GREEN
COLOR_INDEX = colorama.Fore.WHITE

# ---------------------------- HELP -----------------------------------
HELP_CLIENT = "%s------- AVAILABLE CLIENT COMMANDS --------------\n" \
              "%s/put_topic name\n" \
              "/get_topic_list\n" \
              "/switch_topic num\n" \
              "/help\n" \
              "/exit\n" \
              "%s------------------------------------------------\n%s" % \
              (COLOR_DIV_LINES, COLOR_COMMAND, COLOR_DIV_LINES, colorama.Fore.RESET)


# ------------------------ PRINTS --------------------------
def debug_print(text):
    print("%sDEBUG:%s" % (COLOR_DEBUG, text))


def server_msg_print(date, text, end="\n"):
    print("\r%s[%s]:%sSERVER:%s%s " % (COLOR_DATE, date, COLOR_SERVER_NAME, COLOR_TEXT, text), end=end)


def help_print():
    print(HELP_CLIENT)


# ------------------------ WRITE --------------------------------
def write_loop(s, connected, name):
    while connected:
        # TODO
        break

    debug_print("\rDISCONNECTION IN WRITE LOOP")
    os._exit(0)


# ------------------------- READ -------------------------------
def read_loop(s, connected):
    while connected:
        opcode, data = PacketProcessor.parse_packet(s.recv(BUFFER_SIZE))

        if opcode == PacketProcessor.OP_SERVER_MSG:
            # TODO
            debug_print("OP_SERVER_MSG isn't processed")

        elif opcode == PacketProcessor.OP_ANSW_PRODCUTS:
            # TODO
            debug_print("OP_ANSW_PRODCUTS isn't processed")

        elif opcode == PacketProcessor.OP_DISC:
            debug_print("RECEIVED OP_DISC FROM SERVER(%s)" % data["data"]["reason"])
            connected = False
            continue

        else:
            raise Exception("Undefined opcode = %d" % opcode)

    debug_print("\rDISCONNECTION IN READ LOOP")
    os._exit(0)


# ----------------------------------------------------------------
def main():
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
    s.connect((TCP_IP, TCP_PORT))

    # Authorization
    name = input("Print your name: ")
    send_packet = PacketProcessor.get_registration_packet(name=name)
    s.send(send_packet)

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
