import pigpio
import json
import math

def map(val, min_start, max_start, min_finish, max_finish):
    return ((val - min_start) / (max_start - min_start)) * (max_finish - min_finish) + min_finish
    
pi = pigpio.pi()
    
servo_pins = [
    25,
    8,
    7,
    16,
    20,
    21,
]

angles = [0 for i in range(len(servo_pins))]

with open('servo_offsets.json', 'r') as file:
    offsets = json.load(file)

for i, servo_pin in enumerate(servo_pins):
    # gpio.setup(servo_pin, gpio.OUT)

    # p = gpio.PWM(servo_pin, 50)
    # p.start(map(offsets[str(servo_pin)], 0, 180, 2.5, 12.5))
    
    # pwm.append(p)
    pi.set_servo_pulsewidth(servo_pin, map(offsets[i], 0, 180, 500, 2500))
    
    
def set_a(servo, a):
    if servo < len(servo_pins):
        
        a = math.degrees(a)
        angles[servo] = a
        off = offsets[servo]
        try:
            pi.set_servo_pulsewidth(servo_pins[servo], map(a + off, 0, 180, 500, 2500))
        except:
            print('Angle Not in Range')
            
def move_a(servo, i):
    if servo < len(servo_pins):
        a = angles[servo] + math.degrees(i)
        angles[servo] = a
        off = offsets[servo]
        try:
            pi.set_servo_pulsewidth(servo_pins[servo], map(a + off, 0, 180, 500, 2500))
        except:
            print('Angle Not in Range')