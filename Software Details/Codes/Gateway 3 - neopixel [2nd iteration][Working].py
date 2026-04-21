#Once mini locker accepts input, neopixel lights up into 3 different colours and opens door
#Same buzzer frequencies as the main locker will be integrated to it.
from machine import Pin
import neopixel
import random
import time

n=neopixel.NeoPixel(Pin(12),16)

#removed while loop and incrementation and replaced it with for loop with range
for j in range(0,3):
    
    r=random.randint(0,255)
    g=random.randint(0,255)
    b=random.randint(0,255)
    for i in range(0,16):
        n[i]=(r,g,b)
        print(r,g,b)
        time.sleep(0.1)
        n.write()
            
for j in range(0,16):
    n[j]=(0,0,0)
    time.sleep(0.1)
    n.write()

