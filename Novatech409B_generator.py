'''
Interface for Novatech 409B 2-channel rf generator
Jan 2018, Amar Vutha & Mohit Verma. University of Toronto
Last updated: April 6, 2018
'''
from __future__ import division,print_function
import serial
import numpy as np
import time

class Generator_409B:
    TABLE_HOLD = 25.5 # Dwell time to hold in table mode
    INTERNAL_CLOCK_FREQ = 27000000 #Hz, Optimized since manual value is off
    KP = '10' #Clock constant
    #Note: If you want accurate frequency control, run on internal clock
    def __init__(self,address='/dev/ttyUSB1'):
        self.generator = serial.Serial(address,baudrate=19200,stopbits=1,parity='N',timeout=1)
        
    def write(self, command):
        self.generator.write(command+"\n")
        print( self.generator.readlines() )
        
    def reset(self):
        self.generator.write("R\n")
        print( self.generator.readlines() )
        
    def status(self):
        self.generator.write('QUE\n')
        statstring = self.generator.readlines()      # see page 7 of 409B manual for details
        return statstring
        #return [[int(x,16) for x in s.split(' ')] for s in statstring[1:5] ]
    
    def internal_clock(self):
        self.generator.write('C I\n')
        print (self.generator.readlines() )
        return self.generator.readlines() 
    
    def external_clock(self):
        self.generator.write('Kp ' + str(gen.KP)+'\n')
        print( self.generator.readlines() )
        self.generator.write('C E\n')
        print( self.generator.readlines() )
        return self.generator.readlines() 
    
    def set_amplitude(self,amplitude,channel=0):
        # amplitude is an integer between 0 and 1023
        if (amplitude > 1023) or (amplitude < 0): amplitude = 512
        set_amplitude_command = "V" + str(int(channel)) + " " + str(int(amplitude)) + "\n"
        self.generator.write(set_amplitude_command)
        # for s in self.generator.readlines(): print(s)
        
    def set_frequency(self,freq,channel=0):
        #Takes input in MHz
        set_frequency_command = "F" + str(int(channel)) + " " + str(freq) + "\n"
        self.generator.write(set_frequency_command)
        # for s in self.generator.readlines(): print(s)
    
    def set_frequency_external(self, freq, external_clock_freq, channel):
        #Sets frequency 409B is on external clock, takes input in Hz
        F_command = round((freq*int(gen.KP)*gen.INTERNAL_CLOCK_FREQ/(int(gen.KP)*external_clock_freq))/1e6,7)
        set_frequency_command = "F" + str(int(channel)) + " " + str(F_command) + "\n"
        print(set_frequency_command)
        self.generator.write(set_frequency_command)
        return self.generator.readlines() 
        
    def set_phase(self,phase,channel=0):
        # phase is an integer from 0 to 16383
        if (phase > 16383) or (phase < 0): phase = 0
        set_phase_command = "P" + str(int(channel)) + " " + str(phase) + "\n"
        self.generator.write(set_phase_command)
        # for s in self.generator.readlines(): print(s)
        
    def toggle_table(self):
        # Toggles table mode, only works for channels 0 and 1
        toggle_table_command = "M t\n"
        self.generator.write(toggle_table_command)
        
    def table_off(self):
        # Turns table mode OFF, only works for channels 0 and 1
        table_off_command = "M 0\n"
        self.generator.write(table_off_command)    
        
    def table_on(self):
        # Turns table mode ON, only works for channels 0 and 1
        #   turns table OFF first then toggles. Kluge, but works.
        table_off_command = "M 0\n"
        self.generator.write(table_off_command)
        time.sleep(0.010)    
        toggle_table_command = "M t\n"
        self.generator.write(toggle_table_command)
    
    def modulate_channel(self, modulation_freq=1, amplitude_high=int(0.572*1023), channel=0, ncycles=10):
        # modulation_freq in Hz, amplitude_high in bits. Meant for slow modulations 
        for i in range(ncycles):
            set_amplitude_command = "V" + str(int(channel)) + " " + str(int(amplitude_high)) + "\n"
            self.generator.write(set_amplitude_command)
            time.sleep(1/modulation_freq)
            set_amplitude_command = "V" + str(int(channel)) + " " + str(int(0)) + "\n"
            self.generator.write(set_amplitude_command)
            time.sleep(1/modulation_freq)
        return 
        
    def fill_table(self, frequency_array0, phase_array0, amplitude_array0, frequency_array1, phase_array1, amplitude_array1, time_array):
        # All arrays are taken as integers with the following limits:
        # Frequency must be 0 - 171MHz, in units of Hz
        # Phase can be anywhere between 0 to 360
        # Amplitude can be anywhere between 0 and 1V, in units of V
        # Dwell time should be in increments of 100us, in units of ms
        # Enter a dwell time of 25.5 to sustain on the same setting
        
        N = len(frequency_array0)
        
        #Required to enter a table
        table_off_command = "M 0\n" 
        self.generator.write(table_off_command)   
    
        for i in range(N):
            profile_point = hex(i)[2:].zfill(4) 
            frequency0 = hex(int(frequency_array0[i]*10))[2:].zfill(8)
            frequency1 = hex(int(frequency_array1[i]*10))[2:].zfill(8)
            
            phase0 = hex(int(phase_array0[i]/360 * (2**14 - 1)))[2:].zfill(4)
            if (int(phase0, 16) > 16383) or (int(phase0, 16) < 0): phase0 = "0000" #Phase is only up to 14  bits
            phase1 = hex(int(phase_array1[i]/360 * (2**14 - 1)))[2:].zfill(4)
            if (int(phase1, 16) > 16383) or (int(phase1, 16) < 0): phase1 = "0000" #Phase is only up to 14  bits
            
            amplitude0 = hex(int(amplitude_array0[i] * (2**10 - 1)))[2:].zfill(4)
            if (int(amplitude0, 16) > 1023) or (int(amplitude0, 16) < 0): amplitude0 = "0000" #Amplitude is only up to 10  bits
            amplitude1 = hex(int(amplitude_array1[i] * (2**10 - 1)))[2:].zfill(4)
            if (int(amplitude1, 16) > 1023) or (int(amplitude1, 16) < 0): amplitude1 = "0000" #Amplitude is only up to 10  bits
            
            dwell_time = hex(int(time_array[i]*10))[2:].zfill(2) #ff will hold table while 00 will reset it
            
            channel_0_command = "t0 " + profile_point + " " + frequency0 + "," + phase0 + "," + amplitude0 + "," + dwell_time + "\n"
            self.generator.write(channel_0_command)
            channel_1_command = "t1 " + profile_point + " " + frequency1 + "," + phase1 + "," + amplitude1 + "," + dwell_time + "\n"
            self.generator.write(channel_1_command)
        
        '''
        profile_point = hex(N+1)[2:].zfill(4) 
        
        #Closing table
        channel_0_command = "t0 " + profile_point + " " + frequency + "," + phase + "," + amplitude + "," + "00\n"
        self.generator.write(channel_0_command)
        channel_1_command = "t1 " + profile_point + " " + frequency + "," + phase + "," + amplitude + "," + "00\n"
        self.generator.write(channel_1_command)            
        '''

    def advance_table(self):
        self.generator.write("TS\n")
        
    def read_table(self, N, channel = 0):
        # Function needs fixing with processing of datatype. Mohit March 27.
        for i in range(N):
            profile_point = hex(i)[2:].zfill(4) 
            self.generator.write("D" + str(channel) + " " + profile_point + "\n")
            statstring = self.generator.readlines()
            settings = statstring[0].split(',')
            frequency = int(settings[0], 16)/1e7    #MHz
            phase = int(settings[1], 16)/(2**14 -1) * 360
            amplitude = int(settings[2], 16)/1023   #V
            dwell_time = int(settings[3][:2], 16)/10    #ms
            if (dwell_time == 25.5): dwell_time = "Wait for trigger"
            
            print("Profile point: " + str(profile_point))
            print("Frequency: " + str(frequency) + " MHz")
            print("Phase: " + str(phase))
            print("Amplitude: " + str(amplitude) + " V")
            print("Dwell time: " + str(dwell_time) + " ms\n")
                  
    def disable_echo(self):
        self.generator.write("E D\n")
    def save_current_status(self):
        self.generator.write("S\n")
        
    def close(self):
        self.generator.close()
        print("Bye")



gen = Generator_409B('/dev/409B')
gen.disable_echo()
print( gen.status() )

# tests 

## frequency test, channel 0
for i in range(100):
    gen.set_frequency(i*0.1000,channel=1)
    time.sleep(0.1)

## amplitude test, channel 0
gen.set_frequency(1,channel=0)

for i in range(150):
    gen.set_amplitude(i*10,channel=0)
    time.sleep(0.1)

gen.set_amplitude(1000,channel=0)    
for i in range(10):
    gen.set_amplitude(0,channel=2)
    time.sleep(0.5)
    gen.set_amplitude(i*100,channel=2)
    time.sleep(0.5)


## phase test
gen.set_frequency(1,channel=0)
gen.set_amplitude(1000,channel=0)

gen.set_frequency(1,channel=2)
gen.set_amplitude(1000,channel=2)

for i in range(170):
    gen.set_phase(i*100,channel=2)
    time.sleep(0.1)

## Table test
frequency_array0 = [1e6, 1e6]
frequency_array1 = [1e6, 1e6]
phase_array0 = [0, 0]
phase_array1 = [0, 0]
amplitude_array0 = [0, 1]
amplitude_array1 = [0, 1]
time_array = [Generator_409B.TABLE_HOLD, 0]

gen.fill_table(frequency_array0, phase_array0, amplitude_array0, frequency_array1, phase_array1, amplitude_array1, time_array)
gen.write('M t')