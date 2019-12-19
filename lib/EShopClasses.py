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
    def __init__(self, conn, addr, name, key_hash, thread, bank_account):
        self.conn = conn
        self.addr = addr
        self.name = name
        self.key_hash = key_hash
        self.is_connected = False
        self.thread = thread
        self.bank_account = bank_account
        # self.products = []

    def __eq__(self, other):
        return self.name == other.name and self.key_hash == other.key_hash

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

    def add_client(self, client):
        if client not in self.client_list:
            self.client_list.append(client)
        else:
            return False
        return True

    def add_product(self, client, product):
        # self._add_to_client(client, product)
        self._add_to_product_list(product)

    def _add_to_client(self, client, product):
        for client_product in client.products:
            if client_product == product:
                client_product.count += product.count
                return
        client.products.append(product)

    def _add_to_product_list(self, new_product):
        for product in self.product_list:
            if new_product == product:
                product.count += new_product.count
                return
        self.product_list.append(new_product)

    def disconnect_client(self, reason, client):
        if client.is_connected:
            print("DISCONNECTING:Client = %s (%s)" % (client.name, reason))
            send_packet = PacketProcessor.get_disc_packet(reason)
            client.conn.send(send_packet)   
            client.is_connected = False
        # self.client_list.remove(client)

        client.conn.close()

    def disconnect_all_clients(self):
        print("CLIENTS DISCONNECTING")
        for client in self.client_list:
            self.disconnect_client(reason="server closed", client=client)

    def buy_product(self, client, pr_id, count):
        if self.product_list[pr_id].count < count:
            return "Asking for %d %s, but have %d" % (
                count, self.product_list[pr_id].name, self.product_list[pr_id].count)

        if client != self.product_list[pr_id].owner:
            if client.bank_account < self.product_list[pr_id].price * count:
                return "Ops, seems you don't have enough money"

            client.bank_account -= self.product_list[pr_id].price * count
            self.product_list[pr_id].owner.bank_account += self.product_list[pr_id].price * count

        if self.product_list[pr_id].count == count:
            ans = "Oh yeah, You bought all %s" % self.product_list[pr_id].name
            del self.product_list[pr_id]
            return ans
        else:
            self.product_list[pr_id].count -= count
            return "You bought %d %s" % (count, self.product_list[pr_id].name)
