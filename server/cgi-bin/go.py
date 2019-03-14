#!/usr/bin/env python

import cgi
import time
import serial

print "Content-Type: text/html\n"

ser = serial.Serial('/dev/ttyS0', 9600)

form = cgi.FieldStorage()
command = form["cmd"].value
value = form["val"].value

cmd = str(command) + str(value)
ser.write(cmd)

print "done"

