import time
import serial
import signal
import requests
import subprocess

from serial import serialutil
from RepeatedTimer import RepeatedTimer

plants = {}
arduino = None

def timeout(signum, frame):
    print("Command timed out")
    raise Exception("timedOutException")

def connectToArduino(plant_id):
    tty_found = None
    cmd = "find /dev/serial/by-path/. -maxdepth 1 -type l -ls | grep ttyUSB*"
    while True:
        time.sleep(1)
        tty_found = subprocess.run([cmd], shell=True, stdout=subprocess.PIPE)
        if tty_found.returncode == 0:
            tty = "".join(["/dev/", tty_found.stdout.decode().split('/')[-1].strip('\n')])
            print("Found serial device  at",tty)
            plants[plant_id] = serial.Serial(port=tty, baudrate=9600, timeout=2)
            time.sleep(1)
            plants[plant_id].flushInput()
            plants[plant_id].flushOutput()
            plants[plant_id].read_all()
            return plants[plant_id]
            
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

def start(plant_id):
    plants[plant_id] = plant_id
    arduino = None
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(60)
    try:
        plants[plant_id] = connectToArduino(plant_id)
        signal.alarm(0)
    except Exception as exc:
        plants[plant_id] = None
        print(exc)
    if plants[plant_id]:
        print("Arduino found, starting daemon")
        stats = None
        cmd_d = None
        try:
            stats = RepeatedTimer(3, sendStatus, plant_id)
            cmd_d = RepeatedTimer(5, getCommand, plant_id)
        except:
            stats.stop()
            cmd_d.stop()

        finally:
            arduino.close()
    
if __name__ == '__main__':
    start()