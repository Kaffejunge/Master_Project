import XP3000
import Arduino
import Stirrer
import time
import csv
from multiprocessing import Process, Value


class Synthesis():

    outlets = ['waste', 'aq', 'org', 'rct', 'phase',
               'sm1', 'sm2', 'sm3', 'sm4', 'naoh', 'hcl']

    phase_dead_vol = '900'

    def sanity_check(self):
        pass
    #     volume = 'max_vol_' + _to
    #     if((self.updating_vals[_from]-mL) < 0):
    #         print(
    #             f'ERROR! The Volume of {_from} is going to be {self.updating_vals[_from]}\n')
    #         x = input(
    #             'I stopped everything until you are sure about this. Click any Key to continue on your own risk.')

    #     if((self.updating_vals[_to]+mL) > self.const_vals[volume]):
    #         print(
    #             f'The value of {self.updating_vals[_to]+mL} is going to be higher than the set limit of {self.const_vals[volume]} for the {volume} FLASK\n')
    #         x = input(
    #             'I stopped everything until you are sure about this. Click any Key to continue on your own risk.')

    def __init__(self, path_to_csv):
        self.const_vals = {
            'max_vol_rct': 350, 'max_vol_phase': 600, 'max_vol_org': 240, 'max_vol_aq': 240}
        self.updating_vals = {'last_prime': '', 'since_primed': 0, 'rct': 0,
                              'phase': 50, 'org': 0, 'aq': 0}

        self.csv_f = open(path_to_csv, 'r')
        self.reader = csv.reader(self.csv_f)

        self.Pump = XP3000.XP3000('COM30')
        self.Rct_stirrer = Stirrer.Stirrer('COM4')
        self.Wash_stirrer = Stirrer.Stirrer('COM5')
        self.Arduino = Arduino._Arduino('COM3')

    def run(self, check=False):
        if(check):
            self.sanity_check()
            check = False
            self.csv_f.seek(0)

        try:
            for row in self.reader:
                print(f'\nCurrently performing:\n{row}')
                self.call_csv_line(row)
        except:
            print('The synthesis is finished')

    # def get_csv_rows(self):
    #     return sum(1 for row in self.reader)

    def parse_csv_line(self, row):
        # row = next(self.reader)
        self.step = str(row.pop(0).lower())
        self.args = [int(x) if x.isdigit() else x.lower() for x in row]

    def call_csv_line(self, row):
        self.parse_csv_line(row)
        getattr(self, self.step)(self.args)

    def prime(self, moving_from, repeats=3):

        if(moving_from in ['acetone', 'h2o', 'rct_slv', 'wash_slv']):
            solvent = moving_from
        # ensure propper priming
        if(moving_from in ['aq', 'naoh', 'hcl']):
            solvent = 'h2o'

        elif(moving_from.startswith('sm')):
            solvent = 'rct_slv'

        elif(moving_from in ['rct', 'phase', 'org', 'rotovap']):
            solvent = 'wash_slv'

        elif(moving_from == 'waste'):
            return

        if(self.updating_vals['last_prime'] != solvent or self.updating_vals['since_primed'] >= 5):
            self.Arduino.set_valve(solvent)
            self.Arduino.set_valve('waste')
            self.Pump.send_string('/1gS16IA3000OS14A0G' + str(repeats) + 'R')
            self.Pump.wait_for_ready()
            self.updating_vals['last_prime'] = solvent
            self.updating_vals['since_primed'] = 0

        self.updating_vals['since_primed'] += 1

    def empty(self, args):
        flask = args[0]
        try:
            mL = self.updating_vals[flask]
            print(mL)
            self.move([mL, flask, 'waste'])
            self.updating_vals[flask] = 0
        except:
            print(
                f'Flask {flask} can not be emtied. Only rct, phase, aq, org.')

    def rinse_flask(self, args):
        flask, solvent = args

        if(flask in self.updating_vals.keys()):
            if(self.updating_vals[flask] != 0):
                print(f'{flask} is not empty.')
            else:
                self.move([100, solvent, flask])
                if(flask == 'rct'):
                    self.Rct_stirrer.set_speed(420)
                    time.sleep(25)
                    self.Rct_stirrer.set_speed(0)
                    time.sleep(1)
                if(flask == 'phase'):
                    self.Wash_stirrer.set_speed(420)
                    time.sleep(25)
                    self.Wash_stirrer.set_speed(0)
                    time.sleep(1)
                # this line can be replaced by self.empty([flask])
                self.move([105, flask, 'waste'])
        else:
            print('You entered an invalid flask.')

    def flush(self, args):
        print('flush')
        direction = args[0]
        try:
            solvent = args[1]
        except:
            solvent = 'waste'

        if(direction == 'in'):
            for pos in Synthesis.outlets[1:]:
                self.Arduino.set_valve(pos)
                self.Pump.get_syr_vol(3, pos)
                self.Arduino.set_valve('waste')
                self.Pump.empty_syr()

        if(direction == 'out'):

            for pos in Synthesis.outlets[1:]:
                self.Arduino.set_valve(solvent)
                self.Pump.get_syr_vol(3, pos)
                self.Arduino.set_valve(pos)
                self.Pump.empty_syr()

    def clean_valve(self, args):
        pos, solvent = args
        self.prime(solvent, 2)
        self.Arduino.set_valve(solvent)
        self.Pump.send_string('/1IA1500OR')
        self.Pump.wait_for_ready()
        self.Arduino.set_valve(pos)
        self.Pump.send_string('/1S14gA0A1500G2A0S16A1600R')
        self.Pump.wait_for_ready()
        self.Arduino.set_valve('waste')
        self.Pump.empty_syr()

    def clc_volume(self, mL, _from, _to):
        if(_from in self.updating_vals.keys()):
            self.updating_vals[_from] -= mL
        if(_to in self.updating_vals.keys()):
            # +5 because get contamination in flask
            self.updating_vals[_to] += (mL+5)

    def func(self, args):
        self.Pump.flush_buffers()
        self.prime('wash_slv')
        self.updating_vals['last_prime'] = 'wash_slv'
        self.updating_vals['since_primed'] = 0

    def move(self, args):
        mL, _from, _to = args
        loops, rest = divmod(mL, 5)

        self.prime(_from)

        # +1 so it emptys the flask for sure, but not for reactants
        if(_from in self.updating_vals.keys()):
            # ensure full transfer
            loops += 2
            rest = 0

        for i in range(loops):
            self.Arduino.set_valve(_from)
            self.Pump.get_syr_vol(5, _from)
            self.Arduino.set_valve(_to)
            self.Pump.empty_syr()
            # prime every 50 mL
            if((i % 10 == 0) and (i != 0) and (i != loops-1)):
                self.prime(self.updating_vals['last_prime'], 2)

        if(rest != 0):
            self.Arduino.set_valve(_from)
            self.Pump.get_syr_vol(rest, _from)
            self.Arduino.set_valve(_to)
            self.Pump.empty_syr()

        if(_from == 'waste'):
            return
        self.Pump.send_string('/1S16IA3000OS14A0R')
        self.Pump.wait_for_ready()

        self.clc_volume(mL, _from, _to)

    def stir(self, args):
        speed = args[0]
        self.Rct_stirrer.set_speed(speed)
        self.Wash_stirrer.set_speed(speed)

    def heat(self, args):
        temp = args[0]

        time.sleep(5)

        self.Rct_stirrer.set_temp(temp)

        # if(savety == 'error'):
        #     self.end([])

    def wait(self, args):
        t = args[0]*60
        while t:
            mins, secs = divmod(t, 60)
            timeformat = '{:02d}:{:02d}'.format(mins, secs)
            print(timeformat, end='\r')
            time.sleep(1)
            t -= 1

    def wash(self, args):
        _from, _with, mL_with = args

        def move_to_phase():
            # move solution to phase sep flask
            print(self.updating_vals)
            self.move([self.updating_vals[_from], _from, 'phase'])
            print(self.updating_vals)
            # move washing solution to phase sep flask
            self.move([mL_with, _with, 'phase'])
            print(self.updating_vals)

        def stirr_phase():
            # mix phases properly
            self.Wash_stirrer.set_speed(120)
            time.sleep(5)
            self.Wash_stirrer.set_speed(240)
            time.sleep(5)
            self.Wash_stirrer.set_speed(350)
            time.sleep(5)
            self.Wash_stirrer.set_speed(420)
            time.sleep(10)
            self.Wash_stirrer.set_speed(0)
            time.sleep(10)

        def get_init_values():
            # set lower phase reading
            Phase_Arduino = Arduino._Arduino('COM6', 'Uno')
            self.Arduino.set_valve('phase')
            string_to_send = '/1S16A' + Synthesis.phase_dead_vol + 'R'
            self.Pump.send_string(string_to_send)
            self.Pump.wait_for_ready()
            conduct_start = Phase_Arduino.read_phase_pin()
            print(conduct_start)
            if(conduct_start == 0):
                first_pump = 'aq'
                sec_pump = 'org'
            if(conduct_start == 1):
                first_pump = 'org'
                sec_pump = 'aq'

            self.Arduino.set_valve('waste')
            self.Pump.empty_syr()
            return conduct_start, first_pump, sec_pump

        def pump_out(loops, conduct_start, first_pump):
            conduct_cur = conduct_start

            for _ in range(loops):
                loops -= 1
                self.Arduino.set_valve('phase')
                self.Pump.send_string('/1S17A2500R')

                # ? update value of range to fit time needed to stroke
                for _ in range(2000):

                    time.sleep(0.05)
                    conduct_cur = self.Arduino.read_phase_pin()
                    if(conduct_cur != conduct_start):
                        self.Pump.terminate_movement()
                        print('Phase change detected')
                        self.Pump.send_string('/1P255R')
                        self.Pump.wait_for_ready()
                        break

                self.Arduino.set_valve(first_pump)
                self.Pump.empty_syr()
                if(conduct_cur != conduct_start):
                    break

             # discard phase border
            self.Arduino.set_valve('phase')
            self.Pump.send_string('/1A300R')
            self.Pump.wait_for_ready()
            self.Arduino.set_valve('waste')
            self.Pump.empty_syr()
            return loops

        # ! Actual calling of the functions
        move_to_phase()
        stirr_phase()
        conduct_start, first_pump, sec_pump = get_init_values()
        loops = (int(self.updating_vals['phase']/5)+2)
        loops = pump_out(loops, conduct_start, first_pump)

        self.move([loops, 'phase', sec_pump])

    def end(self, args):
        self.csv_f.close()
        print('Closed csv file.')
        self.Pump.close()
        self.Rct_stirrer.close()
        self.Wash_stirrer.close()


if __name__ == '__main__':
    myS = Synthesis(r'a.csv')
    myS.run()
