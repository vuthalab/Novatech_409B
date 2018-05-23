# Novatech_409B
Python class to control the Novatech Instruments 409B 171 MHz 4-channel signal generator

## Requirements
- pyserial: `pip install pyserial`

## Hardware
The generator is powered using a +5V AC power adapter that plugs into the wall. For serial communication there is a 9-pin DSUB which is connected to a DSUB to USB converter to use it with a computer. Along with those, the back panel also has 2 SMA outputs labeled "TS" and "I/O." TS is used for hardware triggering of the device and I/O is used for faster triggering of hardware. We haven't figured out how to get this feature to work yet should anyone attempt it, be aware that the pin should only voltages between 0 to 3.3V (a 50 Ohm terminator has been added to account for this for use with the pulse generator). Finally, there a BNC on the back that is labeled as "10 MHz REF IN." This is meant for syncing to an external clock but is a little problematic for the following issue:

The 409B comes with an add-on option they call /R which allows for the clock of the 409B to be synced to a 10 MHz reference. We didn't get this option so what the device instead does is divide the 10 MHz reference against its internal clock which runs at ~28 MHz. This leads to doing an annoying calibration which leads to the maximum output frequency being limited to ~61 MHz (171*10/28) which is less than ideal. To see how to do this see section 4.6 - 4.10 in the manual. But if you don't want to deal with the hassle, I suggest doing one of the following:

- Just live with running on internal clock, especially if the type of time sequencing you're doing is on a scale that's larger than 100 ns changes.
- Try having your other devices synced to the clock output of 409B. (Note: I haven't actually tried this since I just went with option 1.)

As for the front panel, it has 4 BNC for outputting the signal with the channels labeled as 0 - 3.

## Software
I won't explain the code I've written in detail since it's pretty easy to follow and well commented. Instead, I'll go over useful functions and modes of operation as well as explain some non-obvious commands that we have. For working with the device, we set up a connection using pyserial which connects to the port that the 409B is connected to. On the Sm2+ experiment we have fixed this port using a udev file (See Wesley's post on udev) but you can just find the explicit name of the port that the 409B is connected to.

Note: An easy way to do is before plugging the device in, open terminal and enter 'find /dev/ttyUSB*' This will display all USB ports currently in use. Then plug in the device again and re-enter the command. The new port that shows up is the port that the 409B is connected to.

(Extra note: A more correct/linux-y way of doing this would be find /dev -name 'ttyUSB*'. In general, the find command allows you to do find <base directory> <options> which makes it very versatile and useful.)

With the right port established, it is as simple as using a gen = Generator_409B('/dev/ttyUSB*) command where * is the port that you found. It is strongly advised to also apply the disable_echo() command. The device is defaulted to echo commands back to the computer which slows down the processing (and isn't necessary).

With connection established, the channels can be programmed independently to output signals using the set_frequency, set_amplitude and set_phase functions. There is no enable/display for the channels but you can emulate this effect by setting your amplitude to 0 for disabling.
The set_frequency function takes inputs in MHz (0 to 171 MHz in increments of 0.1 Hz)
The set_amplitude function takes inputs in bits (0 to 1023 which maps to 0 - 1 V)
The set_phase function takes inputs in bits (0 to 16383 which maps to 0 to 360 degrees)

These functions also have safe guards for silly outputs. So if you put in a value that goes past the boundary, it will by default put them to an allowable value instead.

One additional thing to note is that the 409B outputs voltage to a 50 Ohm load, so there is no compensation like you would expect with a function generator. So depending on the load you're driving, the output voltage seen will be different. I mention this because I thankfully realized this before driving a RF amplifier with twice the voltage that I actually needed.

Other useful functions include the save_current_status() function which allows for the saving of settings to the onboard EEprom. I've also written a modulate_channel() function which can be used for pulsing RF at a user specified frequency. This uses the computer's clock so it isn't meant for important time sequeneces but it's primarily useful for things like aligning AOMs or debugging signals.

Here is a code snippet code I have connecting to the 409B and turning on two of the AOM for my lasers:

'''python
#Setting up Connection
SignalGenerator = Generator_409B('/dev/409B')
SignalGenerator.disable_echo()
SignalGenerator.status()

#Turning on lasers
SignalGenerator.set_amplitude(int(VblueAOM*1023),Blue410LaserChannel) SignalGenerator.set_amplitude(int(V697AOM*1023), Red697LaserChannel) SignalGenerator.set_frequency(AOMcentrefreq.magnitude, Blue410LaserChannel) SignalGenerator.set_frequency(AOMcentrefreq.magnitude, Red697LaserChannel)
'''

<h2>Table Mode</h2>
An extremely useful mode of operation for the 409B  is table mode which allows for the cycling of different settings in a timed or triggered manner (both hardware and software). The table mode works by cycling through different amplitude, phase and frequency settings. The table settings can be loaded by using the fill_table function which takes frequency, amplitude, phase and timearrays for the table. Then the table mode sequence can be turned on and off using the toggle_table() function. Some notes on timing:
<ul>
	<li>The minimum time increment 100 us and the maximum is 25.5 ms (denoted as TABLE_HOLD)</li>
	<li>If time 0 is entered, that setting will return for 100 us and then return to the start of the table</li>
	<li>If TABLE_HOLD/25.5 is entered, the table stays stuck on that setting until it is triggered out of it (either by software or hardware)</li>
	<li>The software trigger can done using the advance_table() and a hardware trigger can be applied with a pulse to the TS port.</li>
</ul>
Some things to note:
<ul>
	<li>The table mode only works for channels 0 and 1 and must be run synchronously (that is, the same times must be used for each step in channel 0 and 1)</li>
	<li>Even if you're only using table mode with one channel, you must fill tables for both 0 and 1</li>
	<li>For hardware triggering, the 409B TS port triggers on a negative edge is. (This is the default and it can't be changed)</li>
	<li>The table settings can be read out using read_table()</li>
</ul>
Here is some sample code that I use for pulsing 2 lasers using the table mode with a hardware trigger from the Pulse Generator:

[code language = 'python']

frequency_array0 = [AOMcentrefreq.to(ureg.Hz).magnitude,
AOMcentrefreq.to(ureg.Hz).magnitude, AOMcentrefreq.to(ureg.Hz).magnitude, AOMcentrefreq.to(ureg.Hz).magnitude, AOMcentrefreq.to(ureg.Hz).magnitude]
phase_array0 = [0, 0, 0, 0, 0]
amplitude_array0 = [0, VblueAOM, 0, 0, 0]
frequency_array1 = [AOMcentrefreq.to(ureg.Hz).magnitude, AOMcentrefreq.to(ureg.Hz).magnitude, AOMcentrefreq.to(ureg.Hz).magnitude, AOMcentrefreq.to(ureg.Hz).magnitude, AOMcentrefreq.to(ureg.Hz).magnitude]
phase_array1 = [0, 0, 0, 0, 0]
amplitude_array1 = [0, 0, 0, V697AOM, 0] #Takes units in volts
time_array = [SignalGenerator.TABLE_HOLD, bluePulseLength.magnitude, delayBetweenPulses.magnitude, redPulseLength.magnitude, 0] #Takes units in milliseconds
SignalGenerator.fill_table(frequency_array0, phase_array0, amplitude_array0, frequency_array1, phase_array1, amplitude_array1, time_array)

[/code]
