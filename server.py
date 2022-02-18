from _thread import start_new_thread
import socket
from packets import *


HOST = "192.168.1.13"
PORT = 25565
DEBUG_SERVER = True

players: list[Player] = []
whos_turn = None


def get_player_from_name(name: str) -> Player:
    for player in players:
        if player.username == name:
            return player


def get_player_whos_turn_it_is() -> Player:
    for player in players:
        if player.username == whos_turn:
            return player


def replace_player(username_to_look_for: str, player_replace_with: Player):
    for count, player in enumerate(players):
        if player.username == username_to_look_for:
            players[count] = player_replace_with
            break
    else:
        players.append(player_replace_with)


def client_connect(_conn: socket.socket):
    global whos_turn
    player_name = None
    while True:
        try:
            packet: ClientPacket = decode_packet(_conn.recv(32768))
            if not packet:
                continue
            player_name: packet.player.username
            if packet.packet_type == PACKET_TYPE_REQUEST_JOIN:
                if get_player_from_name(packet.player.username) is None:
                    # dont send any player information if this packet was a join request
                    _conn.send(encode_packet(ServerPacket(PACKET_TYPE_JOIN_ACCEPTED, [])))
                    replace_player(player_name, packet.player)
                    if len(players) == 0:
                        whos_turn = player_name
                else:
                    _conn.send(encode_packet(ServerPacket(PACKET_TYPE_JOIN_DENIED, [])))
                    _conn.close()
            if packet.packet_type == PACKET_TYPE_REQUEST_GAME_INFO:
                pack_to_send = ServerPacket(PACKET_TYPE_GAME_INFO, players)
                replace_player(player_name, packet.player)
                pack_to_send.information = {"doing_turn": whos_turn}
                _conn.send(encode_packet(pack_to_send))
            if packet.packet_type == PACKET_TYPE_END_TURN:
                current_player_turn = packet.player
                for count, player_next_turn in enumerate(players):
                    if player_next_turn.username == current_player_turn.username:
                        whos_turn = players[divmod(count, len(players)-1)[0]].username
                        break
        except ConnectionResetError:
            if get_player_from_name(str(player_name)) is not None:
                for player in players:
                    if player.username == player_name:
                        players.remove(player)
                        break
            if DEBUG_SERVER:
                print("Player disconnected")
            break


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socks:
    socks.bind((HOST, PORT))
    socks.listen()
    while True:
        start_new_thread(client_connect, (socks.accept()[0],))
