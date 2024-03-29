# -*- coding: utf-8 -*-
import logging
import os
import time

from os import listdir
from os.path import join
from threading import Thread, Lock
from select import select
from Queue import Queue, Empty
from flask import Flask
import requests

scanner_thread = None
logging.basicConfig()
_logger = logging.getLogger(__name__)



try:
    import evdev
except ImportError:
    _logger.error('Necesita instalar evdev')
    evdev = None

app = Flask(__name__)


class ScannerDevice():
    def __init__(self, path):
        self.evdev = evdev.InputDevice(path)
        self.evdev.grab()

        self.barcode = []
        self.shift = False

class Scanner(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.lock = Lock()
        self.status = {'status':'connecting', 'messages':[]}
        self.input_dir = '/dev/input/by-id/'
        self.open_devices = []
        self.barcodes = Queue()
        self.keymap = {
            2: ("1","!"),
            3: ("2","@"),
            4: ("3","#"),
            5: ("4","$"),
            6: ("5","%"),
            7: ("6","^"),
            8: ("7","&"),
            9: ("8","*"),
            10:("9","("),
            11:("0",")"),
            12:("-","_"),
            13:("=","+"),
            # 14 BACKSPACE
            # 15 TAB
            16:("q","Q"),
            17:("w","W"),
            18:("e","E"),
            19:("r","R"),
            20:("t","T"),
            21:("y","Y"),
            22:("u","U"),
            23:("i","I"),
            24:("o","O"),
            25:("p","P"),
            26:("[","{"),
            27:("]","}"),
            # 28 ENTER
            # 29 LEFT_CTRL
            30:("a","A"),
            31:("s","S"),
            32:("d","D"),
            33:("f","F"),
            34:("g","G"),
            35:("h","H"),
            36:("j","J"),
            37:("k","K"),
            38:("l","L"),
            39:(";",":"),
            40:("'","\""),
            41:("`","~"),
            # 42 LEFT SHIFT
            43:("\\","|"),
            44:("z","Z"),
            45:("x","X"),
            46:("c","C"),
            47:("v","V"),
            48:("b","B"),
            49:("n","N"),
            50:("m","M"),
            51:(",","<"),
            52:(".",">"),
            53:("/","?"),
            55:("*","*"),
            # 54 RIGHT SHIFT
            57:(" "," "),
            71:("7","7"),
            72:("8","8"),
            73:("9","9"),
            75:("4","4"),
            76:("5","5"),
            77:("6","6"),
            79:("1","1"),
            80:("2","2"),
            81:("3","3"),
            82:("0","0"),
            # 96 enter
        }

    def lockedstart(self):
        with self.lock:
            if not self.isAlive():
                self.daemon = True
                self.start()

    def set_status(self, status, message = None):
        if status == self.status['status']:
            if message != None and message != self.status['messages'][-1]:
                self.status['messages'].append(message)
        else:
            self.status['status'] = status
            if message:
                self.status['messages'] = [message]
            else:
                self.status['messages'] = []

        if status == 'error' and message:
            _logger.error('Barcode Scanner Error: '+message)
        elif status == 'disconnected' and message:
            _logger.info('Disconnected Barcode Scanner: %s', message)

    def get_devices(self):
        try:
            if not evdev:
                return None

            new_devices = [device for device in listdir(self.input_dir)
                           if join(self.input_dir, device) not in [dev.evdev.fn for dev in self.open_devices]]
            scanners = [device for device in new_devices
                        if ('semico_usb_keyboard-event-kbd' in device.lower()) or ('scann' in device.lower())]
            for device in scanners:
               print ('device = ' + device.lower())  

            for device in scanners:
                _logger.debug('opening device %s', join(self.input_dir,device))
                self.open_devices.append(ScannerDevice(join(self.input_dir,device)))

            if self.open_devices:
                self.set_status('connected','Connected to '+ str([dev.evdev.name for dev in self.open_devices]))
            else:
                self.set_status('disconnected','Barcode Scanner Not Found')

            return self.open_devices
        except Exception as e:
            self.set_status('error',str(e))
            return []

    def release_device(self, dev):
        self.open_devices.remove(dev)

    def get_barcode(self):
        """ Returns a scanned barcode. Will wait at most 5 seconds to get a barcode, and will
            return barcode scanned in the past if they are not older than 5 seconds and have not
            been returned before. This is necessary to catch barcodes scanned while the POS is
            busy reading another barcode
        """
        print "Metodo get_barcode"
        self.lockedstart()

        while True:
            try:
                timestamp, barcode = self.barcodes.get(True, 5)
                if timestamp > time.time() - 5:
                    return barcode
            except Empty:
                return ''

    def get_status(self):
        self.lockedstart()
        return self.status

    def _get_open_device_by_fd(self, fd):
        for dev in self.open_devices:
            if dev.evdev.fd == fd:
                return dev

    def run(self):
        """ This will start a loop that catches all keyboard events, parse barcode
            sequences and put them on a timestamped queue that can be consumed by
            the point of sale's requests for barcode events
        """

        self.barcodes = Queue()

        barcode  = []
        shift    = False
        devices  = None

        while True: # barcodes loop
            devices = self.get_devices()

            try:
                while True: # keycode loop
                    r,w,x = select({dev.fd: dev for dev in [d.evdev for d in devices]},[],[],5)
                    if len(r) == 0: # timeout
                        break

                    for fd in r:
                        device = self._get_open_device_by_fd(fd)

                        if not evdev.util.is_device(device.evdev.fn):
                            _logger.info('%s disconnected', str(device.evdev))
                            self.release_device(device)
                            break

                        events = device.evdev.read()

                        for event in events:
                            if event.type == evdev.ecodes.EV_KEY:
                                # _logger.debug('Evdev Keyboard event %s',evdev.categorize(event))
                                #print ('evdev event %s ', evdev.categorize(event))
                                print ('event code: ', event.code)
                                if event.value == 1: # keydown events
                                    if event.code in self.keymap:
                                        if device.shift:
                                            device.barcode.append(self.keymap[event.code][1])
                                            print 'con shift ', self.keymap[event.code][1]
                                        else:
                                            device.barcode.append(self.keymap[event.code][0])
                                            print "sin shift", self.keymap[event.code][0]
                                    elif event.code == 42 or event.code == 54: # SHIFT
                                        device.shift = True
                                    elif event.code == 15:
                                        device.barcode = []
                                    elif event.code == 14:
                                        device.barcode.pop()
                                    elif event.code == 28 or event.code == 96: # ENTER, end of barcode
                                        print device.barcode
                                        requests.request("GET","https://192.168.100.9:5000/find?codigo="+''.join(device.barcode) , verify=False)
                                        print "Enviando datos a la 192.168.100.9"
                                        _logger.debug('pushing barcode %s from %s', ''.join(device.barcode), str(device.evdev))
                                        self.barcodes.put( (time.time(),''.join(device.barcode)) )
                                        device.barcode = []
                                elif event.value == 0: #keyup events
                                    if event.code == 42 or event.code == 54: # LEFT SHIFT
                                        device.shift = False

            except Exception as e:
                self.set_status('error',str(e))


if evdev:
    scanner_thread = Scanner()
    scanner_thread.get_barcode()


@app.route('/')
def hello():
    return "Hello World! " + scanner_thread.get_barcode() if scanner_thread else None

_logger.info('Empezando la aplicacion...')
print "Empezando app"
if __name__ == '__main__':
    app.run(host='0.0.0.0',port='8000')
