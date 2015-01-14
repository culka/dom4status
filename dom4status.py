#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket
import zlib
import struct
import dom4nations

# Returns a GameStatus object, which contains a NationStatus for each nation.
# The classes explain themselves well enough if you know the game
class NationStatus:

    def __init__(self):
        self.number = -1
        self.name = ""
        self.status = ""
        self.statusnum = 0
        self.connected = False
        self.submitted = 0 # 0 = not, 1 = partially, 2 = submitted
    
class GameStatus:
    
    def __init__(self):
        self.name = ""
        self.era = ""
        self.eranum = 0
        self.timer = -1 # Time to host in milliseconds
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
era = {
    0: "None",
    1: "EA",
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
        
def query(address, port):
    sck = socket.socket()
    sck.settimeout(5.0)
    sck.connect((address, port));
    # Little endian, 'fH', 32 bit message length, message body (char)
    sck.send(struct.pack(PACKET_HEADER, 'f', 'H', 1, 3))
    result = None
    result = sck.recv(512)
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
        gs.timer = dataArray[13]            
        gs.turn = dataArray[-3]
        gs.clientstart = dataArray[-2] == 1
        
        # Care only for the nations in game
        for i in range(PACKET_NATION_INFO_START, PACKET_NATION_INFO_START + PACKET_NUM_NATIONS):
            if dataArray[i] != 0:
                if dataArray[i] == 3:
                    continue # Independents, we don't care about them
                ns = NationStatus()
                ns.number = i - PACKET_NATION_INFO_START
                try:
                    ns.name = dom4nations.nations[ns.number]
                except:
                    ns.name = "Nation " + str(ns.number)
                ns.statusnum = dataArray[i]
                ns.status = status[dataArray[i]]
                ns.submitted = dataArray[i + PACKET_NUM_NATIONS]
                ns.connected = dataArray[i + PACKET_NUM_NATIONS * 2] == 1
                gs.nations.append(ns)
        
        sck.send(struct.pack(PACKET_HEADER, 'f', 'H', 1, 11)) # Bye!
        sck.close()
        
        return gs
