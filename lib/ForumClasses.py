from datetime import datetime
from lib import PacketProcessor
from threading import Lock


# ---------------------------- PRODUCT CLASSES -----------------------------------
class Product:
    def __init__(self, name, price, count, owner):
        self.name = name
        self.price = price
        self.count = count
        self.owner = owner

    def __eq__(self, other):
        return self.name == other.name \
               and self.owner == other.owner \
               and self.price == other.price


# ---------------------------- CLIENT CLASS -----------------------------------
class Client():
    def __init__(self, conn, addr, name, thread, bank_account):
        self.conn = conn
        self.addr = addr
        self.name = name
        self.is_connected = False
        self.thread = thread
        self.current_topic = None
        self.bank_account = bank_account
        self.products = []

    def __str__(self):
        return "%s" % self.name


# ---------------------------- DATA CONTAINER CLASS -----------------------------------
class DataContainer():
    def __init__(self):
        self.client_list = []
        self.product_list = []
        self.mutex = Lock()

    def mock_data(self):
        # TODO
        pass

    def remove_client(self, reason, client):
        print("DISCONNECTING:Client = %s (%s)" % (client.name, reason))
        send_packet = PacketProcessor.get_disc_packet(reason)
        client.conn.send(send_packet)
        client.is_connected = False
        self.client_list.remove(client)

        client.conn.close()

    def remove_all_clients(self):
        print("CLIENTS DELETING")
        for client in self.client_list:
            self.remove_client(reason="server closed", client=client)
