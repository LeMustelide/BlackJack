#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import time
import random

#class player
class Player:
    writer = "" 
    deck = []

    def __init__(self, writer):
        self.writer = writer

    def add_card(self, card):
        self.deck.append(card)
    
    def get_writer(self):
        return self.writer
    
    def get_deck(self,):
        return self.deck

#class dealer
class Dealer:
    deck = []

    def add_card(self, card):
        self.deck.append(card)
    
    def get_deck(self,):
        return self.deck

# Class Table
class Table:
    name = ""
    wait_time = 0
    is_start = False
    players = []
    cards = []
    dealer = Dealer()

    # init method or constructor
    def __init__(self, name):
        self.name = name

    def set_time(self, time):
        self.wait_time = time
    
    def start_game(self):
        time.sleep(int(self.get_wait_time()))
        print('Lancement de la partie.')
        self.is_start = True
        self.cards = generation_deck()
        for player in self.players:
            self.give_card(player, 2)
        self.give_card(self.dealer, 2)

    def get_name(self):
        return self.name
    
    def get_wait_time(self):
        return self.wait_time
    
    def get_is_start(self):
        return self.is_start
    
    def add_player(self, player):
        self.players.append(player)
    
    def get_players(self):
        return self.players
    
    def set_cards(self, cards):
        self.cards = cards
    
    def give_card(self, player, nb):
        for i in range(nb) :
            rdm = random.randrange(0, len(self.cards))
            player.add_card(self.cards[rdm])
            self.cards.remove(self.cards[rdm])

    def get_dealer(self):
        return self.dealer

    def get_players_by_writter(self, writter):
        for player in self.players:
            if player.get_writer() == writter:
                return player

# Class Carte
class Card:
    symbol = ""
    name = ""

    def __init__(self, symbol, name):
        self.symbol = symbol
        self.name = name
    
    def get_symbol(self):
        return self.symbol

    def get_name(self):
        return self.name

    def set_symbol(self, symbole):
        self.symbol = symbole
        
    def set_name(self, name):
        self.name = name

    def get_color(self):
        if self.symbol == "Carreaux" or self.symbol == "Cœurs" :
            return "red"
        else:
            return "black"
    
    def to_string(self):
        return self.name+" "+self.symbol

def generation_deck():
    
    cards = []

    symbols = ["Pique", "Carreau", "Cœur", "Trèfle"]
    names = ["As", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Valet", "Dame", "Roi"]

    for symbol in symbols:
        for name in names:
            tempCard = Card(symbol, name)
            cards.append(tempCard)
    return cards

users = [] # empty list of connected users
tables = [] # Un tableau de partie

#Un tableau de joueurs
#Un tableau de croupiers

async def view_deck(writer, table):
    for player in table.get_players():
        if player.get_writer() == writer:
            for card in player.get_deck():
                msg = card.to_string()
                writer.write(f"{msg}\n".encode())
                await writer.drain()
                #print(card.get_symbol()+" "+card.get_name())


            

async def forward(writer, msg):
    for user in users:
        if user == writer:
            user.write(f"{msg}\n".encode())
            await user.drain()
            
# Gestion joueurs
async def handle_request_joueur(reader, writer):
    addr = writer.get_extra_info('peername')[0]
    users.append(writer)
    
    message = f"Player {addr} is connected."
    print(message)
    await forward(writer, "Bienvenue")

    while True:
        data = await reader.readline()

        # auto quit
        if reader.at_eof() :
            print(f"Socket closed by user {addr}")
            data = b"END"
        message = data.decode().strip()

        # error
        if message is None:
            message = 'null'

        # NAME
        if message.startswith('NAME'):
            if len(tables) == 0 :
                data = b"END"
                await forward(writer, "END")
            else :
                for table in tables:
                    if table.get_name() == message.replace('NAME ','') and table.get_is_start() == False:
                        table.add_player(Player(writer))
                        table.start_game()
                        print("test")
                        await forward(writer, "START")
                        await view_deck(writer,table)
                        await forward(writer, "Carte du donneur : "+table.get_dealer().get_deck()[0].to_string())
                        await forward(writer, ".")
                    else:
                        data = b"END"
                        await forward(writer, "END")
                        break
        if message == "MORE":
            player = table.get_players_by_writter(writer)
            table.give_card(player, 1)
        # quit
        if message == "END":
            message = f"Player {addr} quit."
            print(message)
            users.remove(writer)
            writer.close()
            break
        
        #print(message)
        #await forward(writer, message)


# Gestion croupiers
async def handle_request_croupier(reader, writer):
    addr = writer.get_extra_info('peername')[0]
    users.append(writer)
    
    message = f"Dealer {addr} is connected."
    print(message)
    await forward(writer, "Bienvenue")

    while True:
        data = await reader.readline()
        # quit
        if reader.at_eof() :
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
            message = 'null'

        # NAME
        if message.startswith('NAME'):
            table_temp = Table(message.replace('NAME ',''))

        # TIME
        if message.startswith('TIME'):
            table_temp.set_time(message.replace('TIME ',''))
            tables.append(table_temp)
            for table in tables:
                print(table.get_name(), table.get_wait_time())

        await forward(writer, '')


async def blackjack_server():
    # start a socket server
    server_joueur = await asyncio.start_server(handle_request_joueur, '0.0.0.0', 667)
    server_croupier = await asyncio.start_server(handle_request_croupier, '0.0.0.0', 668)
    addr = server_joueur.sockets[0].getsockname()
    print(f'Serving on {addr}')
    async with server_joueur:
        await server_joueur.serve_forever() # handle requests for ever
    async with server_croupier:
        await server_croupier.serve_forever() # handle requests for ever
    
if __name__ == '__main__':
    asyncio.run(blackjack_server())
    print("Hello World !")