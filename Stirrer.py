import serial


class Stirrer:

    def __init__(self, _port):
        self._port = _port
        self._baudrate = 19200
        self.ser = serial.Serial(port=self._port, baudrate=self._baudrate)
        if(ser.isOpen()):
            self.ser.close()
        self.ser.open()
        print(f'Opened successful connection to Stirrer at port: {self._port}')

    def close(self):
        self.ser.write(b'TP1?')
        self.ser.readline()
        self.ser.close()
        print(f'Closed the connection to Stirrer at port: {self._port}')

    def set_speed(self, speed):
        speed = str(speed).zfill(4).encode()
        string_to_send = b'D=' + speed + b'!'
        self.ser.write(string_to_send)
        self.ser.readline()
        self.ser.readline()

    def set_temp(self, temp):

        # check if thermometer is connected
        if(str(self.ser.readline()).split('TP1=')[1].split('\\r')[0] == '----'):
            print(
                'Please connect a thermometer before heating. Make sure it is in the oil bath.')
        else:

            if(temp > 25):
                self.ser.write(b'H1!')
            else:
                self.ser.write(b'H0!')

            # check what happens when H0! but temp is set to sth.
            speed = str(speed).zfill(3).encode()
            string_to_send = b'TP=' + speed + b'!'
            self.ser.write(string_to_send)
            self.ser.readline()
            self.ser.readline()
