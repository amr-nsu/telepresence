import numpy as np
import cv2, os
from PIL import Image

cap = cv2.VideoCapture(0)
global x_prev
global y_prev
global s_prev
x_prev, y_prev, s_prev = None, None, None

while (True):
    ret, img = cap.read()
    
        
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cascadePath = "haarcascade_frontalface_default.xml"
    faceCascade = cv2.CascadeClassifier(cascadePath)
    faces = faceCascade.detectMultiScale(
    gray, 1.3 , 5
    )
    
    for (x, y, w, h) in faces:
        
        cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0), 2)
        
        s = w * h
        x_n, y_n = x, y
        if x_prev is not None:
         
    
            if (abs(s - s_prev) > 15000):
                if (s > s_prev):
                    print("b")
                else:
                    print("f")
            elif (abs(x_prev - x_n) > 25):
                if (x_n > x_prev):
                    print("r")
                else:
                    print("l")
            else:
                print("s")
                
            
      
        x_prev, y_prev, s_prev = x, y, s

    print (faces)
    cv2.imshow('Video', img)
    
    k = cv2.waitKey(30)
    if k==27:
        break
cap.release()
cv2.destroyAllWindows()
