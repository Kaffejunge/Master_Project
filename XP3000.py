import serial


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
        if(ser.isOpen()):
            self.ser.close()
        self.ser.open()
        self.ser.reset_input_buffer()

        # initializing the pump
        self.ser.write(b'/1ZR'+XP3000.term_char)
        print(f'Opened successful connection to XP3000 at port: {self._port}')

    def flush_buffers(self):
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        # or
        ser.flushInput()
        ser.flushOutput()
        # or
        ser.flush()

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
        string_to_send = b'/1QR' + XP3000.term_char
        self.ser.write(string_to_send)
        response = self.ser.readline()
        # !check what the pump returns in python and adjust if statement
        while(response != ''):
            # wait 100 ms
            time.sleep(0.1)
            self.ser.write(string_to_send)
            response = self.ser.readline()

    def set_syr_vol(self, mL):
        # set plunger so syringe contains mL
        muL = int(mL * 1000)
        self.plunger_pos = str(int(muL * (3000/5000))).encode()
        string_to_send = b'/1A' + self.plunger_pos + b'R' + XP3000.term_char
        self.ser.write(string_to_send)
        wait_for_ready()

    def empty_syr(self):
        string_to_send = b'/1A0R' + XP3000.term_char
        self.ser.write(string_to_send)
        self.plunger_pos = 0
        wait_for_ready()

    def terminate_movement(self):
        self.ser.write(b'/1T' + XP3000.term_char)
        self.ser.write(b'/1?R' + XP3000.term_char)
        self.plunger_pos = self.ser.readline()

    def close(self):
        self.ser.close()
        print(f'Closed the connection to XP3000 at port: {self._port}')


pump = XP3000('COM30')
pump.close()
