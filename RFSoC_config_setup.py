### CAN ONLY BE USED IN THE SAME NETWORK WITH XILINX

from ssh import SSH
from create_json import import_json_file, save_list_to_json_file, create_json

# Specify the file name and content
file_name = "config_file.py"
file_content ='''
# Import the QICK drivers and auxiliary libraries
from qick import *
from qick.parser import load_program
# Load bitstream with custom overlay
soc = QickSoc()

soccfg = soc
freqA = {"res_phase": 90 , # The phase of the signal
        "pulse_gain": 2000, # [DAC units]
        "pulse_freq": soccfg.adcfreq(1000, gen_ch=0, ro_ch=0), # [MHz]
        }
freqB = {"res_phase": 180 , # The phase of the signal

        "pulse_gain": 3000, # [DAC units]
        "pulse_style": "const", # --Fixed
        "pulse_freq": soccfg.adcfreq(1000, gen_ch=0, ro_ch=0), # [MHz]
        }
A = "freqA"
B = "freqB"
configEOM={"out_ch":[0,1],
        "freqA": freqA,
        "freqB": freqB,
        "freq_seq": [A,B,A,B],
        "time_seq":[50, 190,370,700],
        "length":100, # [Clock ticks]
        "pulse_freq":soccfg.adcfreq(1000, gen_ch=0, ro_ch=0), #readout freq
        "zone": 1,
        "mode": "periodic",
       }

#TTL
configAOM={
        "length":[[200,200,200,200],[200,200,200,200],[200,200,200,200],[200,200,200,200]], # [Clock ticks]
        "pins":[1,2,0,3],
        "time":[[0,400,800,1200],[0,400,800,1200],[0,400,800,1200],[0,400,800,1200]],
       }
config= {
    "adc_trig_offset": 100, # [Clock ticks]
    "soft_avgs":1,
    # "zone": 1,
    "relax_delay":1.0, # --us
    #Readout
    "readout_length": 2000, # [Clock ticks]
    # "pulse_freq":soccfg.adcfreq(1000, gen_ch=0, ro_ch=0),
    "reps":1, # --Fixed
    "EOM":configEOM,
    "AOM":configAOM
    }

from create_json import import_json_file, save_list_to_json_file, create_json
create_json(config)
'''

# Open the file in write mode and write the content
with open(file_name, "w") as file:
    file.write(file_content)

RFSoC = SSH("129.129.131.153","xilinx","xilinx")
RFSoC.connect()
RFSoC.transfer_file(r"config_file.py",r"/home/xilinx/jupyter_notebooks/qick/qick_demos/config_file.py")
RFSoC.run_code("config_file")
RFSoC.download_file(r"/home/xilinx/jupyter_notebooks/qick/qick_demos/config.json",r"config.json")
RFSoC.disconnect()
# print(config)