import serial
import time
from multiprocessing import Process


class XP3000:

    term_char = chr(13).encode()

    def __init__(self, _port):
        # pump settings
        self.plunger_pos = 0

        # serial settings
        self._port = _port
        self._baudrate = 9600
        # !try ser = serial.rs485.RS485
        self.ser = serial.Serial(
            port=self._port, baudrate=self._baudrate, timeout=5)

        # open the connection
        if(self.ser.isOpen()):
            self.ser.close()
        self.ser.open()
        self.ser.reset_input_buffer()

        # initializing the pump
        self.ser.write(b'/1ZR'+XP3000.term_char)
        print(f'Opened successful connection to XP3000 at port: {self._port}')
        time.sleep(5)

    def flush_buffers(self):
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

    def report(self):
        self.ser.write(b'/1?R' + XP3000.term_char)
        self.plunger_pos = self.ser.readline()
        print(f'Absolute position of plunger: {self.plunger_pos}')

        self.ser.write(b'/1?1R' + XP3000.term_char)
        start_vel = self.ser.readline()
        print(f'Start velocity of plunger: {start_vel}')

        self.ser.write(b'/1?2R' + XP3000.term_char)
        top_vel = self.ser.readline()
        print(f'Top velocity of plunger {top_vel}')

        self.ser.write(b'/1?3R' + XP3000.term_char)
        cutoff_vel = self.ser.readline()
        print(f'Cutoff velocity of plunger: {cutoff_vel}')

        self.ser.write(b'/1?4R' + XP3000.term_char)
        actual_pos = self.ser.readline()
        print(f'Actual position of plunger: {actual_pos}')

        self.ser.write(b'/1?12R' + XP3000.term_char)
        backlash_steps = self.ser.readline()
        print(f'Backlash steps: {backlash_steps}')

        self.ser.write(b'/1?22R' + XP3000.term_char)
        fluid_val = self.ser.readline()
        print(f'Fluid Sensor value (0 = wet): {fluid_val}')

        self.ser.write(b'/1&R' + XP3000.term_char)
        firmware = self.ser.readline()
        print(f'Firmware: {firmware}')

    def wait_for_ready(self):
        # ser.in_waiting() / ser.out_waiting() checks how many bytes at port
        # !check if ser.read_until("'", size=?) works.
        self.flush_buffers()
        string_to_send = b'/1QR' + XP3000.term_char
        ready = False
        while(not ready):
            self.ser.write(string_to_send)
            time.sleep(1)
            response = self.ser.readline()
            ready = "`" in str(response)
            # print(response, ready)

    def get_syr_vol(self, mL, pos, speed=16):
        # set plunger so syringe contains mL
        muL = int(mL * 1000)
        self.plunger_pos = str(int(muL * (3000/5000))).encode()
        solvents = ['acetone', 'h2o', 'rct_slv', 'wash_slv']
        if(pos in solvents):
            string_to_send = b'/1S' + \
                str(speed).encode() + b'IA' + \
                self.plunger_pos + b'R' + XP3000.term_char
        else:
            string_to_send = b'/1S' + \
                str(speed).encode() + b'OA' + \
                self.plunger_pos + b'R' + XP3000.term_char
        # print(string_to_send)
        self.ser.write(string_to_send)
        time.sleep(1)

        self.wait_for_ready()

    def empty_syr(self, speed=14):

        string_to_send = b'/1OS' + \
            str(speed).encode() + b'A0R' + XP3000.term_char
        self.ser.write(string_to_send)
        # self.plunger_pos = 0

        self.wait_for_ready()

    def terminate_movement(self):
        self.ser.write(b'/1T' + XP3000.term_char)
        self.ser.write(b'/1?R' + XP3000.term_char)
        # time.sleep(0.5)
        # self.plunger_pos = self.ser.readline() Needs to be parsed
        self.wait_for_ready()

    def send_string(self, string_to_send):
        string_to_send = string_to_send.encode() + XP3000.term_char
        self.ser.write(string_to_send)
        time.sleep(0.5)

    def read_line(self):
        print(self.ser.readline())

    def set_speed(self, speed):
        # enter number between 1-40 (1 = fastes)
        string_to_send = b'/1S' + str(speed).encode() + b'R' + XP3000.term_char
        self.ser.write(string_to_send)
        self.wait_for_ready()
        print(f'Speed was set to {speed}.')

    def close(self):
        self.ser.close()
        print(f'Closed the connection to XP3000 at port: {self._port}')
