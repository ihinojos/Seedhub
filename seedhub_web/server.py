from threading import Thread
import time
import serial
import signal
import requests
import subprocess

from serial import serialutil
from RepeatedTimer import RepeatedTimer

import atexit

class SerialPort(Thread):
    def __init__(self, port=None, baud=9600, timeout=1):
        super().__init__()
        self.ser = serial.Serial()
        self.ser.port = port
        self.ser.baudrate = baud
        self.ser.timeout = timeout
        self.running = False
        atexit.register(self.ser.close) # Make sure the serial port closes when you quit the program.

    def set_port(self, port_num):
        self.ser.port = "COM"+str(port_num)

    def start(self, *args, **kwargs):
        self.running = True
        self.ser.open()
        super().start()
        self.ser.write("c\n".encode("ascii"))

    def run(self):
        while self.running:
            try:
                incomingByte = self.ser.readline()
                decodedByte = incomingByte.decode("ascii")
                print(decodedByte)
            except:
                pass
            # time.sleep(0.01) # You may want to sleep or use readline

plants = {}
arduino = None
plant_id = ""

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
            arduino = serial.Serial(port=tty, baudrate=9600, timeout=2)
            time.sleep(1)
            arduino.flushInput()
            arduino.flushOutput()
            arduino.read_all()
            return arduino
            
def writeToArduino(command):
    arduino.write(bytes(command, 'ascii'))
    time.sleep(.1)
    data = arduino.readline().decode('ascii')
    data.split('\t')
    return data

def getCommand():
    url = 'http://127.0.0.1:5000/serial/get_cmd'
    response = requests.get(url)
    cmd = response.json()
    if cmd["cmd"] != "None":
        writeToArduino(cmd["cmd"])
    
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
    except serialutil.SerialException:
        return
    
def start(id):
    plant_id = id
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
        print("Arduino found, starting daemon")
        stats = RepeatedTimer(3, sendStatus)
        cmd_d = RepeatedTimer(5, getCommand)
        while True:
            data = input("Type 0 to terminate:")
            if data == '0' : break
            #writeToArduino(arduino, data)
        stats.stop()
        cmd_d.stop()
    arduino.close()

if __name__ == '__main__':
    start("")