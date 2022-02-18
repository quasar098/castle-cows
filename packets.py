import pickle
from cows import *

# client packet types
PACKET_TYPE_REQUEST_GAME_INFO = -2
PACKET_TYPE_REQUEST_JOIN = -3
PACKET_TYPE_END_TURN = -4

# server packet type
PACKET_TYPE_JOIN_DENIED = -15
PACKET_TYPE_JOIN_ACCEPTED = -16
PACKET_TYPE_GAME_INFO = -17


class ClientPacket:
    def __init__(self, packet_type: int, player: Player):
        self.packet_type = packet_type
        self.player = player
        self.information = {}  # packet information such as join request name etc


class ServerPacket:
    def __init__(self, packet_type: int, players: list[Player]):
        self.packet_type = packet_type
        self.players = players
        self.information = {}  # packet information such as join request denied reason


def encode_packet(packet: Union[ClientPacket, ServerPacket]) -> bytes:
    return pickle.dumps(packet)


def decode_packet(packet: bytes) -> Union[ClientPacket, ServerPacket]:
    return pickle.loads(packet)
