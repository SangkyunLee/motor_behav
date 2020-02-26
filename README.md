# motor_behav
This software allows to control stepper motor with control board: Phidget 1067.
In this project, stepper 3327 was used.

The motor is controlled through a Raspberry PI 3B+ model, a DAQ card (mccdaq:118), digital output (mccdio-152), 
and motor controller(Phidget1067).

The main program (i.e., equip_control.py) provides a simpl GUI interface to control motor with Phidget-1067, mcc-118, mcc-152.
While a electric signal for motor rotation is saved in real-time through mcc-118, which is implemented as a separate process(i.e., multi-process), 
the main program allows to control motor by generating voltage output with mcc-152 and feeding it to motor-controller(i.e., Phidget-1067).

Brife summary of main files:
equip_control.py: main gui program
Stepper_control.py: control interface of Phidget-1067
mcc_daq.py: control for mcc-118
mcc_dio.py: control for mcc-152

