import time
import csv

# basically a copy of Synthesis.py it walks through csv but not performing anything
# it checks for errors  like overflowing flasks or prohibited pumping steps


class Sanity():
    def __init__(self, path_to_csv,):
        self.sanity = True

        self.outlets = ['waste', 'aq', 'org', 'rct', 'phase',
                        'sm1', 'sm2', 'sm3', 'sm4', 'naoh', 'hcl']

        self.solvents = ['h2o', 'acetone', 'rct_slv', 'wash_slv']

        self.volumes = {'rct': 0, 'phase': 0, 'org': 0, 'aq': 0}

        self.max_vals = {
            'rct': 350, 'phase': 700, 'org': 240, 'aq': 240}

        self.csv_f = open(path_to_csv, 'r')
        self.reader = csv.reader(self.csv_f)

    def sanity_check(self):
        # iterate through all csv lines and calling them in call_csv_line()
        for row in self.reader:
            self.call_csv_line(row)
            print('')
            time.sleep(0.1)
        return self.sanity

    def parse_csv_line(self, row):
        # row = next(self.reader)
        self.step = str(row.pop(0).lower())
        self.args = [int(x) if x.isdigit() else x.lower() for x in row]

    def call_csv_line(self, row):
        self.parse_csv_line(row)
        getattr(self, self.step)(self.args)

    def func(self, args):
        pass

    def move(self, args):
        mL, _from, _to = args

        # is the start and destination allowed?
        if _from in self.volumes.keys():
            self.volumes[_from] -= mL
        if _to in self.volumes.keys():
            self.volumes[_to] += mL

            # is the destination overflowing?
            if (self.volumes[_to] > self.max_vals[_to]):
                print(self.step, self.args)
                print(
                    f'The volumen of {_to} is {self.volumes[_to]}, which is higher than the allowed limit of {self.max_vals[_to]}.')
                self.sanity = False

        # is the pumping step allowed?
        if _to in ['sm1', 'sm2', 'sm3', 'sm4', 'naoh', 'hcl'] or _to in self.solvents:
            print(self.step, self.args)
            print(f'You cant move {_from} into {_to}.')
            self.sanity = False

    def stir(self, args):
        speed = args[0]
        if (speed >= 1000 or speed < 0):
            print(self.step, self.args)
            print(
                f'Speed of stirring should be between 0 and 1000 rpm. It is {speed}.')
            self.sanity = False

    def heat(self, args):
        temp = args[0]
        if (temp > 150 or temp < 20):
            print(self.step, self.args)
            print(f'Temperature range goes from 20 to 150. It is {temp}.')
            self.sanity = False

    def wait(self, args):
        t = args[0]
        if (t > 4320):
            print(self.step, self.args)
            print(
                f'The maximum waiting time is set to 3 days or 4320 min. It is {t}.\n Please contact your technican if you want to change that setting.')
            self.sanity = False

    def wash(self, args):
        _from, _with, mL_with = args

        # are the given parameters valid?
        f_check = _from in self.volumes.keys()
        w_check = _with in self.solvents
        if (not f_check or not w_check):
            print(self.step, self.args)
            print(
                f'Choose correct options for the washing step. Currently:\nfrom = {_from}; with = {_with}.')
            self.sanity = False

        # if valid parameters check if possible
        if (f_check and w_check):
            if self.volumes[_from] == 0:
                print(self.step, self.args)
                print(f'{_from} was chosen as from but is empty at the moment.')
                self.sanity = False

            # if possible try moving to check for overflowing vessels
            else:
                self.move([self.volumes[_from], _from, 'phase'])
                self.move([mL_with, _with, 'phase'])

    def empt(self, args):
        flask = args[0]
        if flask not in self.volumes.keys():
            print(self.step, self.args)
            print(f'You cant empty {flask}. And you know why.')
        if self.volumes[flask] == 0:
            print(self.step, self.args)
            print(
                f'{flask} is currently empty. Therefore the function empty has no effect.')
            self.sanity = False

    def evap(self, args):
        print('There is no Rotary evaporator implemented at the time. Please delete the evap func.')
        self.sanity = False

    def end(self, args):
        if(self.sanity):
            print(self.step, self.args)
            print('Everything is fine.')
        else:
            print('Fix the points above and try again.')


if __name__ == '__main__':
    myCheck = Sanity(r'a.csv')
    print(myCheck.sanity_check())
