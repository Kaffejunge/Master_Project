# Master_Project
Python script to control various mashines to create an automated synthesis of basic chemical compounds.

install_from_script.py installs the needed modules that are not preinstalled with python (pyserial, pyfirmata, selenium).

Synthesis.py runs the synthesis. Takes a single csv file in __main__

XP3000.py module for a Cavro XP3000

Stirrer.py module for a Heidolph MR3004
 
Arduino.py module for Knauer solvent switcher with A037 valve drive. Also features basic reading functions.

Sanity_check.py checks if the synthesis is valid. If it does not raise an error it is good to go.

Telegram.py opens Firefox and logs into a Telegram account, writing whenever a step is finished.

__________________________________________________________________________

This repository was created for the purpose of tracking my Master thesis in the field of chemistry.
