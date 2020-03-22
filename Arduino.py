from pyfirmata import Arduino, ArduinoMega, util, pyfirmata
import time

# !After importing this module, give a short wait befor asking for a value!


class _Arduino(ArduinoMega, Arduino):

    # configuration of BINs for each valve position
    # for both Knauer valves and the solvent valve

    SS1_dict = {'waste': [1, 1, 1], 'aq': [1, 1, 0], 'org': [
        1, 0, 1], 'rct': [1, 0, 0], 'phase': [0, 1, 1]}

    SS2_dict = {'sm1': [0, 1, 0, 1, 1, 1], 'sm2': [0, 1, 0, 1, 1, 0], 'sm3': [0, 1, 0,
                                                                              1, 0, 1], 'sm4': [0, 1, 0, 1, 0, 0], 'naoh': [0, 1, 0, 0, 1, 1], 'hcl': [0, 1, 0, 0, 1, 0]}

    solvent_dict = {'acetone': [1, 0, 0, 0], 'h2o': [
        0, 1, 0, 0], 'rct_slv': [0, 0, 1, 0], 'wash_slv': [0, 0, 0, 1]}

    def __init__(self, com_port, board_type='mega'):

        # default board is mega
        # pins are configured with:
        # get_pin(a=analog / d=digital, <pin number>, i=input / o=output / p=pmw
        if(board_type == 'mega'):
            self.board = ArduinoMega(com_port)

            self.pin_list = []
            self.pin_list.append(self.board.get_pin('d:4:o'))
            self.pin_list.append(self.board.get_pin('d:3:o'))
            self.pin_list.append(self.board.get_pin('d:2:o'))
            self.pin_list.append(self.board.get_pin('d:7:o'))
            self.pin_list.append(self.board.get_pin('d:6:o'))
            self.pin_list.append(self.board.get_pin('d:5:o'))

            self.slv_pin_list = []
            self.slv_pin_list.append(self.board.get_pin('d:37:o'))
            self.slv_pin_list.append(self.board.get_pin('d:38:o'))
            self.slv_pin_list.append(self.board.get_pin('d:41:o'))
            self.slv_pin_list.append(self.board.get_pin('d:42:o'))

            for pin in self.pin_list:
                pin.write(1)

            self.set_valve('rct_slv')

        # if it is not an Arduino Mega it is set to Uno
        else:
            self.board = Arduino(com_port)

        # phase pin is alwads D8
        self.pin_phase = self.board.get_pin('d:8:i')

        # check if connection worked
        if(str(self.board) != 'None'):
            # create iterator for continuos sampling
            self.it = util.Iterator(self.board)
            self.it.start()
            print(f'Initialized {self.board}')

    def pin_obj_write(self, pin, val):
        pin.write(val)

    def set_digi_pin(self, pin, val):
        if(val > 1):
            val = 1
        elif(val < 0):
            val = 0
        elif(isinstance(val, float)):
            val = int(round(val))
        elif(isinstance(val, int)):
            self.board.digital[pin].write(val)
        else:
            print(f'value was set to {val}, which makes no sense')

    def set_anal_pin(self, pin, val):
        if(val > 1):
            val = 1
        elif(val < 0):
            val = 0
        elif(isinstance(val, float)):
            self.board.analog[pin].write(val)
            # print(f'Set pin{pin} to {val}')
        else:
            print(f'value was set to {val}, which makes no sense')

    def read_phase_pin(self):
        return self.pin_phase.read()

    def set_valve(self, valve):
        # sanitise inputs
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

        # wait for A037 to finish turning
        time.sleep(0.5)

    def test(self):
        # move through all valve positions
        # !Dont use this function to often in sequence.
        # !It may lead to... electrical problems
        for i in range(len(self.pin_list)):
            self.pin_obj_write(self.pin_list[i], 1)
