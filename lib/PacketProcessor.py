from datetime import datetime
import struct
import json

from lib import CommonConstants
from lib.EShopClasses import DataContainer


# ----------------------------------------------------------------
def parse_packet(packet):
    opcode = -1
    try:
        opcode = struct.unpack("!H", packet[0:2])[0]
        data = json.loads(str(packet[4:].decode(CommonConstants.CODING)))

    except:
        print("PARSE_PACKET:BAD JSON(OPCODE = %d\nJSON = %s" % (opcode, str(packet[4:].decode(CommonConstants.CODING))))
        opcode = OP_DISC
        data = {"data": {"reason": "BAD PARSING"}}

    return opcode, data


# ----------------------------------------------------------------
OP_SERVER_MSG = 1


def get_server_msg_packet(text, date):
    json_text = json.dumps({"data": {"text": text, "date": date}})
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       OP_SERVER_MSG,
                       len(json_text),
                       json_text.encode())


# ----------------------------------------------------------------
OP_ADD_PRODUCT = 2


def get_add_product_packet(name, price, count):
    json_text = json.dumps({"data": {"name": name, "price": price, "count": count}})
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       OP_ADD_PRODUCT,
                       len(json_text),
                       json_text.encode())


# ----------------------------------------------------------------
OP_BUY_PRODUCT = 3


def get_buy_product_packet(id, count):
    json_text = json.dumps({"data": {"id": id, "count": count}})
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       OP_BUY_PRODUCT,
                       len(json_text),
                       json_text.encode())


# ----------------------------------------------------------------
OP_REQ_PRODUCTS = 4


def get_req_prodcuts_packet():
    json_text = json.dumps({"data": {"empty": "empty"}})
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       OP_REQ_PRODUCTS,
                       len(json_text),
                       json_text.encode())


# ----------------------------------------------------------------
OP_ANSW_PRODCUTS = 5


def get_answ_prodcuts_packet(dc: DataContainer):
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

    json_text = json.dumps(
        {"data": {"ids": ids, "names": names, "prices": prices, "counts": counts, "owner_names": owner_names}})
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       OP_ANSW_PRODCUTS,
                       len(json_text),
                       json_text.encode())


# ----------------------------------------------------------------
OP_FILL_UP_BA = 6


def get_fill_up_ba_packet(num):
    json_text = json.dumps({"data": {"money": num}})
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       OP_FILL_UP_BA,
                       len(json_text),
                       json_text.encode())


# ----------------------------------------------------------------
OP_DISC = 0


def get_disc_packet(reason):
    json_text = json.dumps({"data": {"reason": reason}})
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       OP_DISC,
                       len(json_text),
                       json_text.encode())


# ----------------------------------------------------------------
OP_REGISTRATION = 7


def get_registration_packet(name, client_hash):
    json_text = json.dumps({"data": {"name": name, "client_hash": client_hash}})
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       OP_REGISTRATION,
                       len(json_text),
                       json_text.encode())
