import argparse

import colorama
from datetime import datetime
import os
import re
import socket
from threading import Thread

from lib.CommonConstants import BUFFER_SIZE
from lib import PacketProcessor
from lib.ForumClasses import DataContainer, Client, Product
from pandas import DataFrame

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
              "get_products\n" \
              "get_clients\n" \
              "help\n" \
              "exit\n" \
              "%s-------------------------------------------------\n%s" % (
                  COLOR_DIV_LINES, COLOR_COMMAND, COLOR_DIV_LINES, colorama.Fore.RESET)


def debug_print(text):
    print("%sDEBUG:%s%s" % (colorama.Fore.RED, text, colorama.Fore.RESET))


def verbose_print(text):
    print("%sVERBOSE:%s%s" % (colorama.Fore.GREEN, text, colorama.Fore.RESET))


# ---------------------------------- CMD INPUT  ----------------------------------------------
def cmd_processing(dc: DataContainer):
    while True:
        command = re.sub(" +", " ", input())
        if command.lower() == "exit":
            exit_server(dc)
        elif command.lower() == "get_products":
            print(DataFrame(get_products(dc)))
        elif command.lower() == "get_clients":
            print(DataFrame(get_clients(dc)))
        elif command.lower() == "help":
            print(HELP_SERVER)
        else:
            print("Undefined command = %s. Use help for information" % command)


def get_products(dc: DataContainer):
    ids = []
    names = []
    prices = []
    counts = []
    owner_names = []

    for id, product in enumerate(dc.product_list):
        ids.append(id)
        names.append(product.name)
        prices.append(product.price)
        counts.append(product.count)
        owner_names.append(product.owner.name)

    return {"id": ids, "name": names, "price": prices, "count": counts, "owner_name": owner_names}


def get_clients(dc: DataContainer):
    ids = []
    names = []
    accounts = []
    ips = []
    is_connected = []

    for id, client in enumerate(dc.client_list):
        ids.append(id)
        names.append(client.name)
        accounts.append(client.bank_account)
        ips.append(client.addr[0])
        is_connected.append(client.is_connected)

    return {"id": ids, "name": names, "bank_account": accounts, "ips": ips,
            "is_connected": is_connected}


def client_registration(dc, new_client):
    while True:
        opcode, data = PacketProcessor.parse_packet(new_client.conn.recv(BUFFER_SIZE))

        if opcode == PacketProcessor.OP_REGISTRATION:
            new_client.name = data["data"]["name"]
            if dc.add_client(new_client):  # registration
                new_client.is_connected = True
                verbose_print("New client = %s(%d) accepted" % (new_client.name, new_client.conn.fileno()))
                send_packet = PacketProcessor.get_registration_packet(new_client.name)
                new_client.conn.send(send_packet)
                return new_client
            else:  # authorization
                for client in dc.client_list:
                    if client == new_client:
                        client.addr = new_client.addr
                        client.conn = new_client.conn
                        new_client = client
                        break
                send_packet = PacketProcessor.get_registration_packet(new_client.name)
                new_client.conn.send(send_packet)
                send_packet = PacketProcessor.get_server_msg_packet(
                    text="You already have account %s. Your bank account = %d" % (
                        new_client.name, new_client.bank_account), date="now")
                new_client.conn.send(send_packet)
                new_client.is_connected = True
                return new_client

        elif opcode == PacketProcessor.OP_DISC:
            new_client.is_connected = False
            return new_client

        else:
            print("opcode = %d (%d awaiting)" % (opcode, PacketProcessor.OP_REGISTRATION))
            send_packet = PacketProcessor.get_disc_packet("NO NAME MESSAGE SENDED")
            new_client.conn.send(send_packet)
            dc.disconnect_client(reason="BAD OPCODE OF INIT MESSAGE", client=new_client)
            new_client.is_connected = False
            return new_client


# ---------------------------- client_processing -----------------------------------
def client_processing(client: Client, dc: DataContainer):
    client = client_registration(dc, client)

    # -------------------- process client loop -----------------------------------
    while client.is_connected:
        opcode, data = PacketProcessor.parse_packet(client.conn.recv(BUFFER_SIZE))
        send_packet = PacketProcessor.get_disc_packet("BAD OPCODE")
        if opcode == PacketProcessor.OP_ADD_PRODUCT:
            dc.mutex.acquire()
            count = data["data"]["count"]
            new_product = Product(name=data["data"]["name"], price=data["data"]["price"], count=count,
                                  owner=client)
            dc.add_product(client, new_product)
            dc.mutex.release()
            verbose_print("Product %s added" % data["data"]["name"])
            send_packet = PacketProcessor.get_server_msg_packet("Your product added", "now")

        elif opcode == PacketProcessor.OP_BUY_PRODUCT:
            ans = dc.buy_product(client, data["data"]["id"], data["data"]["count"])
            verbose_print("Client %s: %s" % (client.name, ans))
            send_packet = PacketProcessor.get_server_msg_packet(
                "%s.Your bank account = %d" % (ans, client.bank_account), "now")

        elif opcode == PacketProcessor.OP_REQ_PRODUCTS:
            send_packet = PacketProcessor.get_answ_prodcuts_packet(dc)

        elif opcode == PacketProcessor.OP_FILL_UP_BA:
            verbose_print("%s bank account = %d + %d" % (client.name, client.bank_account, data["data"]["money"]))
            client.bank_account += data["data"]["money"]
            send_packet = PacketProcessor.get_server_msg_packet("Your bank account = %d" % client.bank_account, "now")

        elif opcode == PacketProcessor.OP_DISC:
            dc.disconnect_client(reason="DISCONNECTION OPCODE == %d" % opcode, client=client)
            break

        else:
            raise Exception("Undefined opcode = %d" % opcode)

        client.conn.send(send_packet)

    print("DISCONNECTED:Client = %s" % client.name)


# ---------------------------------- EXIT----------------------------------
def exit_server(dc: DataContainer):
    dc.disconnect_all_clients()
    print("SERVER EXITING")
    os._exit(0)


# ---------------------------------- MAIN ----------------------------------
def main():
    dc = DataContainer()
    dc.mock_data()
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
        raise Exception("-p port was't passed")

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
        new_client.thread.start()


if __name__ == '__main__':
    main()
