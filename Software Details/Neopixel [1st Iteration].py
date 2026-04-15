#lighting neopixel for correct code when locker opens pass [Main locker - Green, buzzer]
#Iteration 1 with pushbutton
#import modules
from machine import Pin
import time
import neopixel

n=neopixel.NeoPixel(Pin(18),16)
s=Pin(4,Pin.IN,Pin.PULL_UP)
i=-1

while True:
  s_val=s.value()
  if s_val==0:  
    n[i]=(0,255,0)
    time.sleep(0.1)
    n.write()
    i+=1
