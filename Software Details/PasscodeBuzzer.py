#10 different buzzer frequencies for 10 pushbuttons (user entering OTP on locker through pushbuttons)
#import modules
from machine import Pin,PWM
import time
import random

#variables
pb1=Pin(13,Pin.IN,Pin.PULL_UP) #push button 1
pb2=Pin(12,Pin.IN,Pin.PULL_UP) #push button 2
pb3=Pin(14,Pin.IN,Pin.PULL_UP) #push button 3
pb4=Pin(27,Pin.IN,Pin.PULL_UP) #push button 4
pb5=Pin(26,Pin.IN,Pin.PULL_UP) #push button 5
pb6=Pin(4,Pin.IN,Pin.PULL_UP) #push button 6
pb7=Pin(5,Pin.IN,Pin.PULL_UP) #push button 7
pb8=Pin(18,Pin.IN,Pin.PULL_UP) #push button 8
pb9=Pin(19,Pin.IN,Pin.PULL_UP) #push button 9
pb10=Pin(21,Pin.IN,Pin.PULL_UP) #push button 10
b=PWM(Pin(33,Pin.OUT)) #buzzer

#functions
#pushbutton
def pushbutton1():
    pv1=pb1.value()
    time.sleep(0.001)
    if pv1==0:
        b.duty(512)
        for x in range(800,900,1):
            b.freq(x)
            time.sleep(0.001)
            print(1)
    else:
        b.duty(0)
def pushbutton2():
    pv2=pb2.value()
    time.sleep(0.001)
    if pv2==0:
        b.duty(512)
        for x in range(900,1000,1):
            b.freq(x)
            time.sleep(0.001)
            print(2)
    else:
        b.duty(0)
def pushbutton3():
    pv3=pb3.value()
    time.sleep(0.001)
    if pv3==0:
        b.duty(512)
        for x in range(1000,1100,1):
            b.freq(x)
            time.sleep(0.001)
            print(3)
    else:
        b.duty(0)
def pushbutton4():
    pv4=pb4.value()
    time.sleep(0.001)
    if pv4==0:
        b.duty(512)
        for x in range(1100,1200,1):
            b.freq(x)
            time.sleep(0.001)
            print(4)
    else:
        b.duty(0)
def pushbutton5():
    pv5=pb5.value()
    time.sleep(0.001)
    if pv5==0:
        b.duty(512)
        for x in range(1200,1300,1):
            b.freq(x)
            time.sleep(0.001)
            print(5)
    else:
        b.duty(0)
def pushbutton6():
    pv6=pb6.value()
    time.sleep(0.001)
    if pv6==0:
        b.duty(512)
        for x in range(1300,1400,1):
            b.freq(x)
            time.sleep(0.001)
            print(6)
    else:
        b.duty(0)
def pushbutton7():
    pv7=pb7.value()
    time.sleep(0.001)
    if pv7==0:
        b.duty(512)
        for x in range(1400,1500,1):
            b.freq(x)
            time.sleep(0.001)
            print(7)
    else:
        b.duty(0)
def pushbutton8():
    pv8=pb8.value()
    time.sleep(0.001)
    if pv8==0:
        b.duty(512)
        for x in range(1500,1600,1):
            b.freq(x)
            time.sleep(0.001)
            print(8)
    else:
        b.duty(0)
def pushbutton9():
    pv9=pb9.value()
    time.sleep(0.001)
    if pv9==0:
        b.duty(512)
        for x in range(1600,1700,1):
            b.freq(x)
            time.sleep(0.001)
            print(9)
    else:
        b.duty(0)
def pushbutton10():
    pv10=pb10.value()
    time.sleep(0.001)
    if pv10==0:
        b.duty(512)
        for x in range(1700,1800,1):
            b.freq(x)
            time.sleep(0.001)
            print(10)
    else:
        b.duty(0)
      

while True:
    pushbutton1()
    pushbutton2()
    pushbutton3()
    pushbutton4()
    pushbutton5()
    pushbutton6()
    pushbutton7()
    pushbutton8()
    pushbutton9()
    pushbutton10()


