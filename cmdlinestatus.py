#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import dom4status

if len(sys.argv) < 3:
    print "Usage: comdlinestatus *ADDRESS* *PORT*"
else:
    gs = dom4status.query(sys.argv[1],int(sys.argv[2]))
                
    if gs != None:
        print "Name: " + gs.name
        print "Era: " + gs.era
        print "Time to host:" + str(gs.timer)
        
        print "Client start: " + str(gs.clientstart)
        print "Running: " + str(gs.running)
        for i in gs.nations:
            print i.name
            print i.status
            print "Connected: " + str(i.connected)
            print "Submitted: " + str(i.submitted)