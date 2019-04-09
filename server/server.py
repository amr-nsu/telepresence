import serial
import picamera
import socketserver
from threading import Lock
from http import server
from os import curdir, sep
import io
import numpy as np
import cv2, os
from PIL import Image

PAGE="""\
<html>
<head>
<title>picamera MJPEG streaming demo</title>
</head>
<body>
<h1>PiCamera MJPEG Streaming Demo</h1>
<img src="stream.mjpg" width="640" height="480" />
</body>
</html>
"""
def auto(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)                        
    cascadePath="haarcascade_frontalface_default.xml"
    faceCascade = cv2.CascadeClassifier(cascadePath)
    faces = faceCascade.detectMultiScale(
                           gray, 1.3 , 5
                        )
                        #print(faces)
                       
    cmd = None                   
    for (x, y, w, h) in faces:                  
        cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)
        s = w * h
        x_n, y_n = x, y
        x_ref = 320 / 2
        s_ref = 30000 / 4
        print(s, s_ref)
        if (abs(s - s_ref) > 5000 / 2):
            if (s > s_ref):
                cmd = 'b' #HTTPHandler.ser.write('b'.encode())
            else:
                cmd = 'f' #HTTPHandler.ser.write('f'.encode())
        elif (abs(x_ref - x_n - w / 2) > 64 / 2):
            if (x_n > x_ref):
                cmd = 'r' #HTTPHandler.ser.write('r'.encode())
            else:
                cmd = 'l' #HTTPHandler.ser.write('l'.encode())
        else:
            cmd = 's'    #HTTPHandler.ser.write('s'.encode())    
        
    return cmd  

global mode_auto
mode_auto = False 

global ser
ser = serial.Serial('/dev/ttyACM0', 9600)


global counter
counter = 0

class StreamingOutput(object):
    def __init__(self):
        self.lock = Lock()
        self.frame = io.BytesIO()
        self.clients = []

    def write(self, buf):
        global counter
        counter += 1
        died = []
        if buf.startswith(b'\xff\xd8'):
            # New frame, send old frame to all connected clients
            size = self.frame.tell()
            if size > 0:
                self.frame.seek(0)
                data = self.frame.read(size)

                global mode_auto
                print("mode", mode_auto)
                
                if mode_auto and counter % 10 == 0:              
                    frame = np.fromstring(self.frame.getvalue(), dtype=np.uint8)
                    frame = cv2.imdecode(frame, 1)
                    frame = cv2.resize(frame, (0,0), fx=0.5, fy=0.5)
 
                    kuda = auto(frame)
                    if kuda is not None:
                        print("kuda:", kuda)
                        ser.write(kuda.encode())
#                    cv2.imshow(frame)
                       
                self.frame.seek(0)
                with self.lock:
                    for client in self.clients:
                        try:
                            client.wfile.write(b'--FRAME\r\n')
                            client.send_header('Content-Type', 'image/jpeg')
                            client.send_header('Content-Length', size)
                            client.end_headers()
                            client.wfile.write(data)#bilo data
                            client.wfile.write(b'\r\n')
                        except Exception as e:
                            died.append(client)
        self.frame.write(buf)
        if died:
            self.remove_clients(died)

    def flush(self):
        with self.lock:
            for client in self.clients:
                client.wfile.close()

    def add_client(self, client):
        print('Adding streaming client %s:%d' % client.client_address)
        with self.lock:
            self.clients.append(client)

    def remove_clients(self, clients):
        with self.lock:
            for client in clients:
                try:
                    print('Removing streaming client %s:%d' % client.client_address)
                    self.clients.remove(client)
                except ValueError:
                    pass # already removed


class HTTPHandler(server.BaseHTTPRequestHandler):
#    ser = serial.Serial('/dev/ttyACM0', 9600)

    def do_GET(self):
        if self.path == '/':
            self.path += 'index.html'
        if self.path.endswith(".html") or self.path.endswith(".js") or self.path.endswith(".svg") or self.path.endswith(".css"):
            self.send_response(200)
            self.end_headers()
            try:
                f = open(curdir + sep + self.path)
                self.wfile.write(bytes(f.read(), 'utf-8'))
                f.close()
            except IOError as e:
                self.send_error(404, str(e))
        elif self.path == '/stream.mjpg':
            self.close_connection = False
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=--FRAME')
            self.end_headers()
            output.add_client(self)
        if 'cmd=' in self.path:
            self.send_response(200)
            self.end_headers()
            cmd = self.path.split('cmd=')[1][0]
            if (cmd=='a'):
                global mode_auto
                mode_auto = not mode_auto
            else:
                #global ser
                ser.write(cmd.encode())



if __name__ == '__main__':   

    class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
        pass
 
    with picamera.PiCamera(resolution=(640, 480), framerate=24) as camera:
        output = StreamingOutput()
        camera.start_recording(output, format='mjpeg')
        try:
            address = ('', 8000)
            server = StreamingServer(address, HTTPHandler)
            server.serve_forever()
        finally:
            camera.stop_recording()
