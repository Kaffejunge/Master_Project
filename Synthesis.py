import XP3000
import Arduino
import Stirrer
import time
import Telegram
import csv
import Sanity_check

# This code is opensource. Licence can be found on https://github.com/Kaffejunge/Master_Project.git

# before running this code make sure you have installed pyserial and pyfirmate or run the provided lib_installation.py

# for configuring your ports use:
# python -m serial.tools.list_ports


class Synthesis():
    outlets = ['waste', 'aq', 'org', 'rct', 'phase',
               'sm1', 'sm2', 'sm3', 'sm4', 'naoh', 'hcl']

    phase_dead_vol = '900'

    def __init__(self, path_to_csv, telegram_nr=''):

        self.updating_vals = {'last_prime': '', 'since_primed': 0, 'rct': 90,
                              'phase': 0, 'org': 0, 'aq': 0}

        # check if reporting via telegram is desired
        self.reporting = False
        if(telegram_nr.isdigit() and telegram_nr.startswith('1')):
            self.reporting = True
            self.Reporter = Telegram.Telegram(telegram_nr)

        # read provided csv file with key words
        self.csv_f = open(path_to_csv, 'r')
        self.reader = csv.reader(self.csv_f)

        # initialize all used equipment if necessarry
        self.Arduino = Arduino._Arduino('COM3')
        self.Pump = XP3000.XP3000('COM30')
        self.Rct_stirrer = Stirrer.Stirrer('COM11', heating=True)

    def run(self):
        # this function is the only one called from outside the class
        # it calls all lines in sequence and executes the specified function
        try:
            for row in self.reader:
                print(f'\nCurrently performing:\n{row}')
                if(self.reporting):
                    self.Reporter.report(row)
                self.call_csv_line(row)
        except:
            # if something fails end all connections, which turns of heating etc as well
            if(self.reporting):
                self.Reporter.report('The Synthesis has ended.')
            print('The synthesis has ended')
            self.end('')

    def parse_csv_line(self, row):
        self.step = str(row.pop(0).lower())
        self.args = [int(x) if x.isdigit() else x.lower() for x in row]

    def call_csv_line(self, row):
        self.parse_csv_line(row)
        getattr(self, self.step)(self.args)

    def prime(self, moving_from, repeats=3):
        # primes the loop with repeats*5 mL

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
            # if air is aspirated no priming is necessary
            return

        # prime if previous prime is different from the required one or it has been more than 4 moving steps since the last prime
        if(self.updating_vals['last_prime'] != solvent or self.updating_vals['since_primed'] >= 4):
            self.Arduino.set_valve(solvent)
            self.Arduino.set_valve('waste')
            self.Pump.send_string('/1gS16IA3000OS14A0G' + str(repeats) + 'R')
            self.Pump.wait_for_ready()
            self.updating_vals['last_prime'] = solvent
            self.updating_vals['since_primed'] = 0
        print(f'Primed with {solvent}.')

        self.updating_vals['since_primed'] += 1
        if(self.reporting):
            if(repeats == 3):
                self.Reporter.report(f'Primed with {solvent}.')
            else:
                self.Reporter.report(f'Reprimed with {solvent}.')

    def empt(self, args):
        # moves the content of a flask to the waste
        # allowed flasks are rct, phase, aq, org
        flask = args[0]

        try:
            mL = self.updating_vals[flask]
            print(mL)
            self.move([mL, flask, 'waste'])
            self.updating_vals[flask] = 0
        except:
            print(
                f'Flask {flask} can not be emtied. Only rct, phase, aq, org.')

        if(self.reporting):
            self.Reporter.report(f'Emptied {flask}.')

    def rinse_flask(self, args):
        # moves 100 mL of specified solvent into flask, stirrs if possible and moves it to the waste
        # flask needs to be empty before this function is applicable
        # allowed flasks are rct, phase, aq, org
        flask, solvent = args

        if(flask in self.updating_vals.keys()):
            if(self.updating_vals[flask] != 0):
                print(f'{flask} is not empty.')
            else:
                self.move([100, solvent, flask])

                # set stirring if possible
                if(flask == 'rct'):
                    self.Rct_stirrer.set_speed(420)
                    time.sleep(25)
                    self.Rct_stirrer.set_speed(0)
                    time.sleep(1)
                if(flask == 'phase'):
                    try:
                        Wash_stirrer = Stirrer.Stirrer('COM12')
                        Wash_stirrer.set_speed(420)
                        time.sleep(25)
                        Wash_stirrer.close()
                        time.sleep(1)
                    except:
                        pass

                # this line can be replaced by self.empty([flask])
                self.move([105, flask, 'waste'])

                if(self.reporting):
                    self.Reporter.report(f'Rinsed {flask} with {solvent}.')
        else:
            print('You entered an invalid flask.')

    def flush(self, args):
        # function should only be used by maintenance stuff
        direction = args[0]
        try:
            solvent = args[1]
        except:
            solvent = 'waste'

        if(direction == 'in'):
            for pos in Synthesis.outlets[1:]:
                self.Arduino.set_valve(pos)
                self.Pump.get_syr_vol(3, solvent)
                self.Arduino.set_valve('waste')
                self.Pump.empty_syr()

        if(direction == 'out'):

            # for pos in Synthesis.outlets[1:]:
            for pos in ['sm1', 'sm2', 'sm3', 'sm4']:
                self.Arduino.set_valve(solvent)
                self.Pump.get_syr_vol(5, solvent)
                self.Arduino.set_valve(pos)
                self.Pump.empty_syr()

    def clean_valve(self, args):
        # cleans rotor seal and valve position
        # usefull when operating with aggressive chemicals
        # use only after talking to maintenance stuff
        # after the func is finished the tube is filled with 450 steps of solvent

        # cleans the rotor seal on a specified valve position with specified solvent
        pos, solvent = args
        self.prime(solvent, 2)
        self.Arduino.set_valve(solvent)
        self.Pump.send_string('/1IA666OR')
        self.Pump.wait_for_ready()
        self.Arduino.set_valve(pos)
        self.Pump.send_string('/1S14gA0A666G2A0S16A500R')
        self.Pump.wait_for_ready()
        self.Arduino.set_valve('waste')
        self.Pump.empty_syr()

        self.Arduino.set_valve(solvent)
        self.Pump.send_string('/1IA350OR')
        self.Pump.wait_for_ready()
        self.Arduino.set_valve(pos)
        self.Pump.empty_syr()

        if(self.reporting):
            self.Reporter.report(
                f'I cleaned rotor seal of {pos} with {solvent}.')

    def clc_volume(self, mL, _from, _to):
        # if flask is tracked set new volumes
        if(_from in self.updating_vals.keys()):
            self.updating_vals[_from] -= mL

        if(_to in self.updating_vals.keys()):
            # +5 because get contamination in flask
            self.updating_vals[_to] += (mL+5)

        if(self.reporting):
            self.Reporter.report(f'New values: {self.updating_vals}.')

    def func(self, args):
        # first function of all synthesis. Primes loop.
        self.Pump.flush_buffers()
        self.prime('rct_slv')
        self.updating_vals['last_prime'] = 'slv_slv'

    def move(self, args):
        # right now only integer amount of mL are moved
        mL, _from, _to = args
        loops, rest = divmod(int(mL), 5)

        # prime with correct solvent
        self.prime(_from)

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

        # add 5 mL of contaminated loop solvent to the destination
        self.Pump.send_string('/1S16IA3000OS14A0R')
        self.Pump.wait_for_ready()

        self.clc_volume(mL, _from, _to)
        if(self.reporting):
            self.Reporter.report(f'Moved {mL} mL from {_from} to {_to}.')

    def stir(self, args):
        speed = args[0]
        self.Rct_stirrer.set_speed(speed)
        if(self.reporting):
            self.Reporter.report(f'Stirring set to {speed} rpm.')

    def heat(self, args):
        temp = args[0]
        # optional argument self.Rct_stirrer.set_temp(temp, wait=True) waits for the temperature to be reached
        self.Rct_stirrer.set_temp(temp)

        if(self.reporting):
            self.Reporter.report(f'Temperature is set to {temp} °C.')

    def wait(self, args):
        t = args[0]
        # if waiting time is longer than 10 min all devices are turned off during this time
        # to prevent possible disconnection due to inactivity or some other reason I cant figure out.
        restart = t > 10
        if(restart):
            # close all ports for the waiting time
            self.close_all()
        if(self.reporting):
            self.Reporter.report(f'I will wait now for {t} min.')

        while t:
            mins, secs = divmod(t, 60)
            timeformat = '{:02d}:{:02d}'.format(mins, secs)
            print(timeformat, end='\r')
            time.sleep(1)
            t -= 1

        # restart all devices if turned off previously
        if(restart):
            self.Arduino = Arduino._Arduino('COM3')
            self.Pump = XP3000.XP3000('COM30')
            self.Rct_stirrer = Stirrer.Stirrer('COM11', heating=True)

        if(self.reporting):
            self.Reporter.report('Done waiting.')

    def wash(self, args):
        _from, _with, mL_with = args

        # wash method contains functions

        def move_to_phase():
            # move solution _from to phase separation flask
            self.move([self.updating_vals[_from], _from, 'phase'])
            # move washing solution to phase sep flask
            self.move([mL_with, _with, 'phase'])

            if(self.reporting):
                self.Reporter.report(
                    f'(Washing)Pumped {self.updating_vals[_from]} mL from {_from} and {mL_with} mL from {_with} to the phase flask.')

        def stirr_phase():
            # mix phases properly
            # ramping up speed ensures stirring
            Wash_stirrer = Stirrer.Stirrer('COM12')
            Wash_stirrer.set_speed(120)
            time.sleep(5)
            Wash_stirrer.set_speed(240)
            time.sleep(5)
            Wash_stirrer.set_speed(350)
            time.sleep(5)
            Wash_stirrer.set_speed(420)
            time.sleep(20)
            Wash_stirrer.close()
            time.sleep(20)
            if(self.reporting):
                self.Reporter.report(f'(Washing)Stirred phases.')

        def get_init_values():
            # set lower phase reading by aspirating dead volume and then reading conductivity
            self.Arduino.set_valve('phase')
            string_to_send = '/1S16A' + Synthesis.phase_dead_vol + 'R'
            self.Pump.send_string(string_to_send)
            self.Pump.wait_for_ready()
            conduct_start = self.Arduino.read_phase_pin()

            # setting pump destinations
            if(conduct_start == 0):
                first_pump = 'aq'
                sec_pump = 'org'
            if(conduct_start == 1):
                first_pump = 'org'
                sec_pump = 'aq'

            # moving dead volume to waste
            self.Arduino.set_valve('waste')
            self.Pump.empty_syr()
            if(self.reporting):
                self.Reporter.report(
                    f'Lower phase gave reading {conduct_start}.')

            return conduct_start, first_pump, sec_pump

        def pump_out(loops, conduct_start, first_pump):
            conduct_cur = conduct_start
            # a copy is created from loops, so it can be modified
            out_loops = loops

            if(self.reporting):
                self.Reporter.report(f'(Washing)Started pumping out.')

            # _ is a place holder it works like i
            for _ in range(out_loops):
                loops -= 1
                self.Arduino.set_valve('phase')
                # send_string is used so pump does not wait_for_ready()
                self.Pump.send_string('/1S17A2500R')

                # time the pump needs for one stroke is measured (statements still included but commented out)
                # during that time frame the conductivity is measured every 50 ms
                # if phase change happens the pump is stopped and the loop broken
                for i in range(520):
                    time.sleep(0.05)
                    # start = time.perf_counter()
                    conduct_cur = self.Arduino.read_phase_pin()
                    # print(
                    #     f'It took {time.perf_counter()-start} to read value.')

                    if(conduct_cur != conduct_start):
                        self.Pump.terminate_movement()

                        if(self.reporting):
                            self.Reporter.report(
                                f'(Washing)Phase change detected after {(out_loops-loops)*5} mL.')

                        # get dead volume from reading to valve
                        self.Pump.send_string('/1P255R')
                        self.Pump.wait_for_ready()
                        break

                self.Arduino.set_valve(first_pump)
                self.Pump.empty_syr()
                if(conduct_cur != conduct_start):
                    break

            # discard phase border (0.3 mL)
            self.Arduino.set_valve('phase')
            self.Pump.send_string('/1A300R')
            self.Pump.wait_for_ready()
            self.Arduino.set_valve('waste')
            self.Pump.empty_syr()
            # return remaining volume as loop iterations
            return loops

        # !Actual calling of the functions
        move_to_phase()
        stirr_phase()
        conduct_start, first_pump, sec_pump = get_init_values()
        loops = (int(self.updating_vals['phase']/5)+2)
        remain_loops = pump_out(loops, conduct_start, first_pump)

        # move the remaining mL
        self.move([remain_loops*5, 'phase', sec_pump])
        if(self.reporting):
            self.Reporter.report(f'(Washing)Finished.')

    def close_all(self):
        # closes all serial connections
        self.csv_f.close()
        self.Pump.close()
        self.Rct_stirrer.close()
        self.Wash_stirrer.close()

    def end(self, args):
        self.close_all()

        if(self.reporting):
            self.Reporter.report('The Synthesis is finished.')
        print('The last line is reached.')


if __name__ == '__main__':
    # perform Sanity check first
    csv = r'a.csv'
    myCheck = Sanity_check.Sanity(csv)

    # if Synthesis is sane run it
    if(myCheck.sanity_check()):
        myS = Synthesis(csv)
        myS.run()
