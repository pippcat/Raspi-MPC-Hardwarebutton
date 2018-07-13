#!/usr/bin/env python
# coding: UTF-8

import RPi.GPIO as GPIO
import Queue, time
import subprocess

def setup():
    print "mpcremote init started"
    global q
    q = Queue.Queue()
    q.put(['green',100, 0])
    GPIO.setmode(GPIO.BOARD)       # Numbers GPIOs by physical location
    # setting up LEDs
    GPIO.setup(8, GPIO.OUT) #green
    GPIO.setup(10, GPIO.OUT) #red
    GPIO.setup(12, GPIO.OUT) #white
    GPIO.setup(16, GPIO.OUT) #blue
    global green, red, blue, white
    green  = GPIO.PWM(8,.5)
    red = GPIO.PWM(10,3)
    blue = GPIO.PWM(16,2)
    white = GPIO.PWM(12,3)
    green.start(0)
    red.start(0)
    blue.start(0)
    white.start(0)

    # setting up switches
    global SGreen, SBlue, SRed, SWhite
    SGreen = 18 # Play/Pause
    SBlue = 22 # next song
    SRed = 24 # volume up
    SWhite = 26 # volume down
    GPIO.setup(SGreen, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(SBlue, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(SRed, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(SWhite, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # stopping mpd
    subprocess.call("mpc stop", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def flashLED():
    while not q.empty():
        tasks=q.get() # ["color", int(dutycycle), int(delay)]
        if tasks[0] == "white":
            white.ChangeDutyCycle(tasks[1])
        if tasks[0] == "green":
            green.ChangeDutyCycle(tasks[1])
        if tasks[0] == "blue":
            blue.ChangeDutyCycle(tasks[1])
        if tasks[0] == "red":
            red.ChangeDutyCycle(tasks[1])
        time.sleep(tasks[2])

def remote():
    print "mpcremote process started"
    Play = False
    while True:
        SGreen_Status = GPIO.input(SGreen)
        SRed_Status = GPIO.input(SRed)
        SBlue_Status = GPIO.input(SBlue)
        SWhite_Status = GPIO.input(SWhite)
        if SGreen_Status == False and SWhite_Status == False:
            print('switch event: reset')
            q.put(['green',50,0])
            q.put(['white',50,0])
            q.put(['red',50,0])
            q.put(['blue',50,3])
            q.put(['green',100,0])
            q.put(['white',0,0])
            q.put(['red',0,0])
            q.put(['blue',0,0])
            subprocess.call("sudo reboot 0", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        elif SGreen_Status == False:
            Play = not Play
            if Play:
                print('switch event: play')
                q.put(['green',33,0.2])
                flashLED()
            else:
                print('switch event: pause')
                q.put(['green',100,0.2])
                flashLED()
            subprocess.call("mpc toggle", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print subprocess.check_output(["mpc", "status"])
        elif SRed_Status == False:
            print('switch event: volume up')
            subprocess.call("mpc vol +10", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print subprocess.check_output(["mpc", "status"])
            q.put(['red',20,1])
            flashLED()
            q.put(['red',0,0])
            flashLED()
        elif SBlue_Status == False:
            subprocess.call("mpc next", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print('switch event: next song')
            print subprocess.check_output(["mpc", "status"])
            q.put(['blue',50,1])
            flashLED()
            q.put(['blue',0,0])
            flashLED()
            if not Play:
                q.put(['green',33,0.2])
                flashLED()
                Play = not Play
        elif SWhite_Status == False:
            print('switch event: volume down')
            subprocess.call("mpc vol -10", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print subprocess.check_output(["mpc", "status"])
            q.put(['white',20,1])
            flashLED()
            q.put(['white',0,0])
            flashLED()
        time.sleep(0.02)
        flashLED()


def destroy():
    green.stop()
    red.stop()
    blue.stop()
    white.stop()
    GPIO.cleanup()                  # Release resource
    # stopping mpd
    subprocess.call("mpc stop", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print " pressed, process killed"
    print subprocess.check_output(["mpc", "status"])


if __name__ == '__main__':     # Program start from here
    setup()
    try:
        remote()
    except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program destroy() will be  executed.
        destroy()