import time
import serial
import signal
import requests
import subprocess

from serial import serialutil
from RepeatedTimer import RepeatedTimer

arduino = None

def timeout(signum, frame):
    print("Command timed out")
    raise Exception("timedOutException")

def connectToArduino():
    tty_found = None
    cmd = "find /dev/serial/by-path/. -maxdepth 1 -type l -ls | grep ttyUSB*"
    while True:
        time.sleep(1)
        tty_found = subprocess.run([cmd], shell=True, stdout=subprocess.PIPE)
        if tty_found.returncode == 0:
            tty = "".join(["/dev/", tty_found.stdout.decode().split('/')[-1].strip('\n')])
            print("Found serial device  at",tty)
            arduino = serial.Serial(port=tty, baudrate=9600, timeout=.2)
            time.sleep(1)
            arduino.flushInput()
            arduino.flushOutput()
            arduino.read_all()
            return arduino

def writeToArduino(command):
    arduino.write(bytes(command, 'ascii'))
    time.sleep(.1)
    try:
        data = arduino.readline().decode('ascii')
        data.split('\t')
        return data
    except:
        return None

def getCommand():
    url = 'http://127.0.0.1:5000/serial/get_cmd'
    response = requests.get(url)
    cmds = response.json()
    for cmd in cmds["cmds"]:
        print(cmd)
        if cmd != "None":
            writeToArduino(cmd)

def sendStatus():
    url = 'http://127.0.0.1:5000/api/save_info'
    arduino.write(bytes('<read_info,0>', 'ascii'))
    time.sleep(.1)
    try:
        status = arduino.readline().decode('ascii')
        status = status.split('\t')
        if len(status) == 4:
            data = {}
            for stat in status:
                log = stat.split(':')
                data[log[0]] = log[1].strip('\r\n')
            response = requests.post(url, json=data)
            #print(response.content)
    except:
        pass

if __name__ == '__main__':
    arduino = None
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(60)
    try:
        arduino = connectToArduino()
        signal.alarm(0)
    except Exception as exc:
        arduino = None
        print(exc)
    if arduino:
        try:
            print("Arduino found, starting daemon")
            getCommand()
            stats = RepeatedTimer(3, sendStatus)
            cmd_d = RepeatedTimer(60, getCommand)
            while True:
                data = input("Type 0 to terminate:")
                if data == '0' : raise Exception
                resp = writeToArduino(data)
                print(resp)
        except:
            stats.stop()
            cmd_d.stop()
            arduino.close() 