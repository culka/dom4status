#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket
import zlib
import struct

# Returns a GameStatus object, which contains a NationStatus for each nation.
# The classes explain themselves well enough if you know the game
class NationStatus:

    def __init__(self):
        self.number = -1
        self.name = ""
        self.status = ""
        self.statusnum = 0
        self.connected = False
        self.submitted = False
    
class GameStatus:
    
    def __init__(self):
        self.name = ""
        self.era = ""
        self.eranum = 0
        self.timer = -1
        self.turn = 0
        self.clientstart = False
        self.running = False
        self.nations = []

PACKET_HEADER = '<ccLB'
PACKET_BYTES_PER_NATION = 3
PACKET_NUM_NATIONS = 200
PACKET_GENARAL_INFO = '<BBBBBB{0}sBBBBBBLB{1}BLLB' # to use format later
PACKET_NATION_INFO_START = 15

# See http://www.cs.helsinki.fi/u/aitakang/dom3_serverformat_notes for descriptions for most of the protocol

# Python 2 doesn't support enums with the standard libraries, so...
era = {1: "EA",
    2: "MA",
    3: "LA"}

status = {
    0: "Empty",
    1: "Human",
    2: "AI",
    3: "Independent",
    253: "Closed",
    254: "Defeated this turn",
    255: "Defeated"}

# Taken from the modding manual
# Maybe make external or support mods or something
nations = {5: "Arcoscephale", # EA
    6: "Ermor",
    7: "Ulm",
    8: "Marverni",
    9: "Sauromatia",
    10: "T'ien Ch'i",
    11: "Machaka",
    12: "Mictlan",
    13: "Abysia",
    14: "Caelum",
    15: "C'tis",
    16: "Pangaea",
    17: "Agartha",
    18: "Tir na n'Og",
    19: "Fomoria",
    20: "Vanheim",
    21: "Helheim",
    22: "Niefelheim",
    25: "Kailasa",
    26: "Lanka",
    27: "Yomi",
    28: "Hinnom",
    29: "Ur",
    30: "Berytos",
    31: "Xibalba",
    83: "Atlantis",
    84: "R'lyeh",
    85: "Pelagia",
    86: "Oceania",
    33: "Arcoscephale", # MA
    34: "Ermor",
    35: "Sceleria",
    36: "Pythium",
    37: "Man",
    38: "Eriu",
    39: "Ulm",
    40: "Marignon",
    41: "Mictlan",
    42: "T'ien Ch'i",
    43: "Machaka",
    44: "Agartha",
    45: "Abysia",
    46: "Caelum",
    47: "C'tis",
    48: "Pangaea",
    49: "Asphodel",
    50: "Vanheim",
    51: "Jotunheim",
    52: "Vanarus",
    53: "Bandar Log",
    54: "Shinuyama",
    55: "Ashdod",
    87: "Atlantis",
    88: "R'lyeh",
    89: "Pelagia",
    90: "Oceania",
    57: "Nazca",
    58: "Xibalba",
    60: "Arcoscephale", # LA
    61: "Pythium",
    62: "Lemuria",
    63: "Man",
    64: "Ulm",
    65: "Marignon",
    66: "Mictlan",
    67: "T'ien Ch'i",
    69: "Jomon",
    70: "Agartha",
    71: "Abysia",
    72: "Caelum",
    73: "C'tis",
    74: "Pangaea",
    75: "Midgård",
    76: "Utgård",
    77: "Bogarus",
    78: "Patala",
    79: "Gath",
    80: "Ragha",
    91: "Atlantis",
    92: "R'lyeh",
    81: "Xibalba"}
    
class StatusQuery:
    
    def __init__(self, address, port):
        self.socket = socket.socket()
        self.address = address
        self.port = port
        self.socket.settimeout(5.0)
    
    def query(self):
        self.socket.connect((self.address, self.port));
        # Little endian, 'fH', 32 bit message length, message body (char)
        self.socket.send(struct.pack(PACKET_HEADER, 'f', 'H', 1, 3))
        result = None
        result = self.socket.recv(512)
        if result != None:
            if len(result) < 50:
                print "error, received packet is not long enough"
                return None
            
            header = struct.unpack(PACKET_HEADER, result[0:7])
            compressed = (header[1] == 'J')
            packetlength = header[2]
            packettype = header[3]
                        
            data = None
                                    
            if (compressed):
                data = zlib.decompress(result[10:])
            else:
                data = result[10:]
                        
            gamenamelength = len(data) - len(PACKET_GENARAL_INFO.format("", "")) - PACKET_BYTES_PER_NATION * PACKET_NUM_NATIONS - 6
            
            dataArray = struct.unpack(PACKET_GENARAL_INFO.format(gamenamelength, PACKET_BYTES_PER_NATION * PACKET_NUM_NATIONS), data)
            
            gs = GameStatus()
            
            gs.running = dataArray[5] == 2
            gs.name = dataArray[6]
            gs.eranum = dataArray[7]
            gs.era = era[gs.eranum]
            gs.timer = dataArray[9]            
            gs.turn = dataArray[-3]
            gs.clientstart = dataArray[-2] == 1
            
            # Care only for the nations in game
            for i in range(PACKET_NATION_INFO_START, PACKET_NATION_INFO_START + PACKET_NUM_NATIONS):
                if dataArray[i] != 0:
                    if dataArray[i] == 3:
                        continue # Independents, we don't care about them
                    ns = NationStatus()
                    ns.number = i - PACKET_NATION_INFO_START
                    ns.name = nations[ns.number]
                    ns.statusnum = dataArray[i]
                    ns.status = status[dataArray[i]]
                    ns.submitted = dataArray[i + PACKET_NUM_NATIONS] == 1
                    ns.connected = dataArray[i + PACKET_NUM_NATIONS * 2] == 1
                    gs.nations.append(ns)
            
            self.socket.send(struct.pack(PACKET_HEADER, 'f', 'H', 1, 11)) # Bye!
            self.socket.close()
            
            return gs
            
