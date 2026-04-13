#servo motor moves only when hand is placed near ultrasound sensor (between 10-15cm) [Math Equation Gateway]
#import modules
from machine import Pin,time_pulse_us,PWM
import time

#variables
trig = Pin(27, Pin.OUT)
echo = Pin(14, Pin.IN)
p=PWM(Pin(4))    #Pin.OUT default hence optional
p.freq(50)

while True:
    trig.off()
    time.sleep_us(2)
    trig.on()
    time.sleep_us(10)
    trig.off()
    duration = time_pulse_us(echo, 1, 30000)  
    if duration < 0:
        print("No object detected (Timeout)")
    else:
        distance = duration / 58
        print("Distance:", distance, "cm")
        if distance>=10 and distance<15:
            for i in range(0,120,1):
                p.duty(i)
                time.sleep(0.01)
            for j in range(120,-1,-1):
                p.duty(j)
                time.sleep(0.01)

    time.sleep(1)

