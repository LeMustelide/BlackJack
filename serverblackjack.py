#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio

# Class Table
class Table:
    name = ""
    wait_time = 0
    is_start = False
    player = []

    # init method or constructor
    def __init__(self, name):
        self.name = name

    def set_time(self, time):
        self.wait_time = time
    
    def start_game(self):
        self.is_start = True

    def get_name(self):
        return self.name
    
    def get_wait_time(self):
        return self.wait_time
    
    def get_is_start(self):
        return self.is_start
    
    def add_player(self, player):
        self.player.append(player)

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

    def get_couleur(self):
        if self.symbol == "Carreaux" or self.symbol == "Cœurs" :
            return "red"
        else:
            return "black"

def generation_deck():
    
    cards = []

    symbols = ["Pique", "Carreau", "Cœur", "Trèfle"]
    names = ["As", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Valet", "Dame", "Roi"]

    i = 0
    for symbol in symbols:
        for name in names:
            i += 1
            tempCard = Card(symbol, name)
            cards.append(tempCard)
    return cards

users = [] # empty list of connected users
tables = [] # Un tableau de partie

#Un tableau de joueurs
#Un tableau de croupiers


async def forward(writer, addr, msg):
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
    await forward(writer, addr, "Bienvenue")

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
                await forward(writer, addr, "END")
            else :
                for table in tables:
                    print("---Choice game---")
                    if table.get_name() == message.replace('NAME ','') and table.get_is_start() == False:
                        table.add_player(writer)
                        asyncio.sleep(table.get_wait_time())
                        table.start_game()
                        print(len(generation_deck()))
                    else:
                        data = b"END"
                        await forward(writer, addr, "END")
                        break
            message = data.decode().strip()

        # quit
        if message == "END":
            message = f"Player {addr} quit."
            print(message)
            await forward(writer, "Server", "END")
            users.remove(writer)
            writer.close()
            break
        
        print(message)
        await forward(writer, addr, message)


# Gestion croupiers
async def handle_request_croupier(reader, writer):
    addr = writer.get_extra_info('peername')[0]
    users.append(writer)
    
    message = f"Dealer {addr} is connected."
    print(message)
    await forward(writer, addr, "Bienvenue")

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
            await forward(writer, "Server", message)
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

        await forward(writer, addr, '')


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