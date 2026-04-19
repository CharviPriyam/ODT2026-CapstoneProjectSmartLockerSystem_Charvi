from machine import Pin
import neopixel
import random
import time

n=neopixel.NeoPixel(Pin(12),16)
c=0

while True:
    
    r=random.randint(0,255)
    g=random.randint(0,255)
    b=random.randint(0,255)
    for i in range(0,16):
        n[i]=(r,g,b)
        print(r,g,b)
        time.sleep(0.1)
        n.write()
    c+=1
    if c==3:
        for i in range(0,16):
            n[i]=(0,0,0)
            n.write()
            time.sleep(0.1)
    if c==4:
        break
    
#loop does not stop
