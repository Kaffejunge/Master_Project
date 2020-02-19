# list all comports from terminal
# python -m serial.tools.list_ports

from pyfirmata import Arduino, util
import time


class _Arduino(Arduino):

    SS1_dict = {'waste': [1, 1, 1], 'aq': [1, 1, 0], 'org': [
        1, 0, 1], 'rct': [1, 0, 0], 'phase': [0, 1, 1]}

    SS2_dict = {'sm1': [0, 1, 0, 1, 1, 1], 'sm2': [0, 1, 0, 1, 1, 0], 'sm3': [0, 1, 0,
                                                                              1, 0, 1], 'sm4': [0, 1, 0, 1, 0, 0], 'naoh': [0, 1, 0, 1, 0, 0], 'hcl': [0, 1, 0, 1, 0, 1]}

    solvent_dict = {'acetone': [1, 0, 0, 0], 'h2o': [
        0, 1, 0, 0], 'rct_slv': [0, 0, 1, 0], 'wash_slv': [0, 0, 0, 1]}

    def __init__(self, com_port):

        self.board = Arduino(com_port)
        self.com_port = com_port

        # get_pin(a=analog / d=digital, <pin number>, i=input / o=output / p=pmw)

        self.pin_list = []
        self.pin_list.append(self.board.get_pin('d:2:o'))
        self.pin_list.append(self.board.get_pin('d:3:o'))
        self.pin_list.append(self.board.get_pin('d:4:o'))
        self.pin_list.append(self.board.get_pin('d:5:o'))
        self.pin_list.append(self.board.get_pin('d:6:o'))
        self.pin_list.append(self.board.get_pin('d:7:o'))

        self.slv_pin_list = []
        self.slv_pin_list.append(self.board.get_pin('d:8:o'))
        self.slv_pin_list.append(self.board.get_pin('d:9:o'))
        self.slv_pin_list.append(self.board.get_pin('d:10:o'))
        self.slv_pin_list.append(self.board.get_pin('d:11:o'))

        # self.pin_phase = self.board.get_pin('a::i')
        # self.pin_rotovap = self.board.get_pin('d::o')

        if(str(self.board) != 'None'):
            # create iterator for continuos sampling
            self.it = util.Iterator(self.board)
            self.it.start()
            print(f'Initialized {self.board}')

    def isDigi(self):
        pass

    def pin_obj_write(self, pin, val):
        pin.write(val)

    def set_digi_pin(self, pin, val):

        if(val > 1):
            val = 1
        elif(val < 0):
            val = 0
        elif(isinstance(val, float)):
            val = int(round(val))

        self.board.digital[pin].write(val)
        # print(f'Set pin{pin} to {val}')

    def set_anal_pin(self, pin, val):
        if(val > 1):
            val = 1
        elif(val < 0):
            val = 0
        elif(isinstance(val, float)):
            val = int(round(val))

        self.board.analog[pin].write(val)
        print(f'Set pin{pin} to {val}')

    def read_anal_pin(self):
        val = self.pin_sampling.read()
        print(val)

    def read_digi_pin(self):
        pass
        # ! Do i need this?

    def set_valve(self, valve):

        valve = str(valve).lower()
        if valve in _Arduino.SS1_dict:
            for i in range(0, 3):
                self.pin_obj_write(
                    self.pin_list[i], _Arduino.SS1_dict[valve][i])

        if valve in _Arduino.SS2_dict:
            for i in range(0, len(self.pin_list)):
                self.pin_obj_write(
                    self.pin_list[i], _Arduino.SS2_dict[valve][i])

        if valve in _Arduino.solvent_dict:
            for i in range(len(self.slv_pin_list)):
                self.pin_obj_write(
                    self.slv_pin_list[i], _Arduino.solvent_dict[valve][i])

    def test(self):
        for i in range(len(self.pin_list)):
            self.pin_obj_write(self.pin_list[i], 1)


myArduino = _Arduino('COM8')
time.sleep(1)
myArduino.set_valve('waste')
time.sleep(1)
myArduino.set_valve('aq')
time.sleep(1)
myArduino.set_valve('org')
time.sleep(1)
myArduino.set_valve('rct')
time.sleep(1)
myArduino.set_valve('phase')
time.sleep(1)
myArduino.set_valve('SM4')
time.sleep(1)


print('Done')
