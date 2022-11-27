#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import random

# class player
class Player:
    writer = ""
    deck = []
    id = 0

    def __init__(self, writer, id):
        self.writer = writer
        self.id = id

    def add_card(self, card):
        self.deck.append(card)

    def get_writer(self):
        return self.writer

    def get_deck(self):
        return self.deck

    def get_id(self):
        return self.id

    def get_score(self):
        sum = 0
        buffer = 0
        for card in self.deck: 
            if card.get_score() != 1:
                sum += card.get_score()
            else:
                buffer += 1
        for i in range(buffer):
            if sum <= 10:
                sum += 11
            else:
                sum += 1
        return sum

# class dealer
class Dealer:
    deck = []

    def add_card(self, card):
        self.deck.append(card)

    def get_deck(self):
        return self.deck

# Class Table
class Table:
    name = ""
    wait_time = 0
    waiting = False
    is_start = False
    players = []
    cards = []
    dealer = Dealer()
    players_finished = 0

    # init method or constructor
    def __init__(self, name):
        self.name = name

    def set_time(self, time):
        self.wait_time = time

    async def start_game(self):
        self.waiting = True
        print(self.get_wait_time())
        await asyncio.sleep(int(self.get_wait_time()))
        self.waiting = False
        print("Lancement de la partie.")
        self.is_start = True
        self.cards = generation_deck()
        for player in self.players:
            print('don carte !!!!'+str(player.get_id()))
            self.give_card(player, 2)
        self.give_card(self.dealer, 2)

    def get_is_waiting(self):
        return self.waiting

    def get_name(self):
        return self.name

    def get_wait_time(self):
        return self.wait_time

    def get_is_start(self):
        return self.is_start

    def add_player(self, player):
        self.players.append(player)

    def remove_player(self, player):
        self.players.remove(player)

    def get_players(self):
        return self.players

    def set_cards(self, cards):
        self.cards = cards

    def increment_player_finished(self):
        self.players_finished += 1
    
    def get_players_finished(self):
        return self.players_finished

    def give_card(self, player, nb):
        for i in range(nb):
            print(str(i))
            rdm = random.randrange(0, len(self.cards))
            player.add_card(self.cards[rdm])
            self.cards.remove(self.cards[rdm])

    def get_dealer(self):
        return self.dealer

# Class Carte
class Card:
    symbol = ""
    name = ""
    score = 0

    def __init__(self, symbol, name, score):
        self.symbol = symbol
        self.name = name
        self.score = score

    def get_symbol(self):
        return self.symbol

    def get_name(self):
        return self.name

    def set_symbol(self, symbole):
        self.symbol = symbole

    def set_name(self, name):
        self.name = name

    def get_color(self):
        if self.symbol == "Carreaux" or self.symbol == "Cœurs":
            return "red"
        else:
            return "black"

    def to_string(self):
        return self.name + " " + self.symbol
    
    def get_score(self):
        return self.score

def generation_deck():

    cards = []

    symbols = ["Pique", "Carreau", "Cœur", "Trèfle"]
    names = ["As", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Valet", "Dame", "Roi"]
    scores = [1,2,3,4,5,6,7,8,9,10,10,10,10]
    i = 0
    for symbol in symbols:
        for name in names:
            tempCard = Card(symbol, name, scores[i])
            cards.append(tempCard)
            i = i + 1
        i = 0
    return cards


users = []  # empty list of connected users
tables = []  # Un tableau de partie

# Un tableau de joueurs
# Un tableau de croupiers


async def view_deck(player):
    for card in player.get_deck():
        msg = card.to_string()
        await forward(player.get_writer(), str(player.get_id())+" "+msg)
    await forward(player.get_writer(), "Score total : "+ str(player.get_score()))

async def forward(writer, msg):
    writer.write(f"{msg}\n".encode())
    await writer.drain()


# Gestion joueurs
async def handle_request_joueur(reader, writer):
    addr = writer.get_extra_info("peername")[0]
    users.append(writer)

    message = f"Player {addr} is connected."
    print(message)
    await forward(writer, "Bienvenue")

    current_player = Player(writer, len(users))
    while True:
        data = await reader.readline()

        # auto quit
        if reader.at_eof():
            print(f"Socket closed by user {addr}")
            data = b"END"
        message = data.decode().strip()

        # error
        if message is None:
            message = "null"

        # NAME
        if message.startswith("NAME"):
            if len(tables) == 0:
                data = b"END"
                await forward(writer, "END")
            else:
                for table in tables:
                    if (
                        table.get_name() == message.replace("NAME ", "")
                        and table.get_is_start() == False
                    ):
                        table.add_player(current_player)
                        if table.get_is_waiting() == False:
                            print("démarrage ...")
                            await table.start_game()
                        while table.get_is_start() == False:
                            await asyncio.sleep(1)
                        await forward(writer, "START")
                        await view_deck(current_player)
                        await forward(
                            writer,
                            "Carte du donneur : "
                            + table.get_dealer().get_deck()[0].to_string(),
                        )
                        send_msg = 1
                        while send_msg == 1 and current_player.get_score() <= 21:
                            await forward(writer, ".")
                            # boucle pour attendre le msg MORE
                            data = await reader.readline()
                            message = data.decode().strip()
                            if message != "":
                                # await forward(writer, message)
                                if message.startswith("MORE 1"):
                                    await forward(writer, "pioche une carte")
                                    table.give_card(current_player, 1)
                                    await view_deck(current_player)
                                    # si le joueur veut piocher une carte
                                else :
                                    send_msg = 0
                        await forward(current_player.get_writer(), "Score finale : "+ str(current_player.get_score()))
                        table.increment_player_finished()
                        while table.get_players_finished() != len(table.get_players()):
                            await asyncio.sleep(10)
                            await forward(current_player.get_writer(), "En attente de la fin de la partie")
                        await forward(current_player.get_writer(), "Fin de la partie")
                    else:
                        data = b"END"
                        await forward(writer, "END")
                        break

        # quit
        if message == "END":
            message = f"Player {addr} quit."
            print(message)
            for table in tables:
                for player in table.get_players():
                    if player.get_writer() == writer:
                        table.remove_player(player)
            users.remove(writer)
            
            writer.close()
            break

        # print(message)
        # await forward(writer, message)

# Gestion croupiers
async def handle_request_croupier(reader, writer):
    addr = writer.get_extra_info("peername")[0]
    users.append(writer)

    message = f"Dealer {addr} is connected."
    print(message)
    await forward(writer, "Bienvenue")

    while True:
        data = await reader.readline()
        # quit
        if reader.at_eof():
            print(f"Socket closed by user {addr}")
            data = b"END"
        message = data.decode().strip()

        if message == "END":
            message = f"Dealer {addr} quit."
            print(message)
            await forward(writer, message)
            users.remove(writer)
            writer.close()
            break

        # error
        if message is None:
            message = "null"

        # NAME
        if message.startswith("NAME"):
            table_temp = Table(message.replace("NAME ", ""))

        # TIME
        if message.startswith("TIME"):
            table_temp.set_time(message.replace("TIME ", ""))
            tables.append(table_temp)
            for table in tables:
                print(table.get_name(), table.get_wait_time())

        await forward(writer, "")


async def blackjack_server():
    # start a socket server
    server_joueur = await asyncio.start_server(handle_request_joueur, "0.0.0.0", 667)
    server_croupier = await asyncio.start_server(
        handle_request_croupier, "0.0.0.0", 668
    )
    addr = server_joueur.sockets[0].getsockname()
    print(f"Serving on {addr}")
    async with server_joueur:
        await server_joueur.serve_forever()  # handle requests for ever
    async with server_croupier:
        await server_croupier.serve_forever()  # handle requests for ever
    while True:
        for table in tables:
            if ( table.is_start() == True and len(table.get_players()) == 0 ) or table.is_end() == True:
                tables.remove(table)


if __name__ == "__main__":
    asyncio.run(blackjack_server())