import subprocess
import sys

list_of_package = ['pyfirmata', 'pyserial']


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


for pack in list_of_package:
    install(pack)
