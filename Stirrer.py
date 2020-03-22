import serial
import time


class Stirrer:

    def __init__(self, _port, heating=False):
        # setting 8N1 with 19200
        self._port = _port
        self._baudrate = 19200
        self.ser = serial.Serial(
            port=self._port, baudrate=self._baudrate, timeout=5)

        # open connection
        if(self.ser.isOpen()):
            self.ser.close()
        self.ser.open()

        # set control via PC
        self.flush_buffers()
        self.ser.write(b'REM!')
        time.sleep(0.5)

        # set heating if specified
        if(heating):
            self.flush_buffers()
            self.ser.write(b'M1!')
            time.sleep(0.5)
            self.flush_buffers()
            self.ser.write(b'H0!')

        print(f'Opened successful connection to Stirrer at port: {self._port}')

    def set_speed(self, speed):
        self.flush_buffers()
        speed = str(speed).zfill(4).encode()
        string_to_send = b'D=' + speed + b'!'
        self.ser.write(string_to_send)
        self.flush_buffers()

    def set_temp(self, temp, wait=False):
        self.flush_buffers()

        if(temp > 25):
            self.flush_buffers()
            time.sleep(0.5)
            self.ser.write(b'H1!')
            print('H1!')

        self.flush_buffers()
        time.sleep(0.5)
        temp = str(temp).zfill(3).encode()
        string_to_send = b'TP=' + temp + b'!'
        self.ser.write(string_to_send)
        time.sleep(0.5)

        # wait for the temp to be reached if needed
        if(wait):
            self.wait_for_temp(temp)

        else:
            self.flush_buffers()
            time.sleep(0.5)
            self.ser.write(b'H0!')
            print('H0!')

    def wait_for_temp(self, temp):
        # get initial values
        response = '0'

        # read TP1? and parse answer until read from probe = set temp
        while(int(response.split(',')[0]) != int(temp)):
            self.flush_buffers()
            time.sleep(5)
            self.ser.write(b'TP1?')
            time.sleep(0.5)
            useless = self.ser.readline()

            # print(f'Useless: {useless}\n')
            if(',' in str(useless)):
                continue
            time.sleep(0.5)
            response = self.ser.readline()
            if(',' not in str(response)):
                response = '0'
                self.flush_buffers()
                continue
            response = str(response).split('TP1=')[1].split('\\r')[0]
            print(
                f"Wanted temp: {int(temp)}C\tCurrent temp: {response}C")

            # if probe gets disconnected perform savety shutdown
            if(response == '----'):
                print(
                    'Please connect a thermometer before heating. Make sure it is in the oil bath.')
                self.flush_buffers()
                self.ser.write(b'TP1=20')
                time.sleep(1)
                self.flush_buffers()
                self.ser.write(b'H0!')
                time.sleep(1)
                return 'error'
        print(
            f"The reaction temperature of {int(response.split(',')[0])} is reached.")
        return 0

    def flush_buffers(self):
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

    def close(self):
        # turn of stirring
        self.flush_buffers()
        self.ser.write(b'D=0000!')
        time.sleep(0.5)
        self.flush_buffers()
        time.sleep(0.5)

        # turn off heating if it is on
        try:
            self.ser.write(b'TP=020!')
            self.flush_buffers()
            time.sleep(0.5)
            self.ser.write(b'H0!')
            self.flush_buffers()
            time.sleep(0.5)
        except:
            pass

        self.flush_buffers()
        self.ser.close()
        print(f'Closed the connection to Stirrer at port: {self._port}')
