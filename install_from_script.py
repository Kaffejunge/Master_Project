import subprocess
import sys


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


list_of_package = ['pyfirmata', 'pyserial']

for pack in list_of_package:
    install(pack)
