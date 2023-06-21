from ssh import SSH
import os
from XMLGenerator import xml_config_to_dict, add_value_to_xml

from create_json import import_json_file, save_list_to_json_file



class RFSoC_controller:
    def __init__(self, host="129.129.131.153", username="xilinx", password="xilinx", config_host=None):
        if config_host==None:
            self.host = host
            self.username = username
            self.password = password
        else:
            self.host = config_host["host"]
            self.username = config_host["username"]
            self.password = config_host["password"]
        self.RFSoC = SSH(host,username,password)
        self.try_connect()

    def try_connect(self):
        try:
            print("Connection was established")
            self.RFSoC.connect()
            return True
        except:
            print("Connection cannot be established")
            return False

    def disconnect(self):
        self.RFSoC.disconnect()

    def build_config(self):
        if not self.get_config():
            self.freqA = {
            "res_phase": 90 , # The phase of the signal
            "pulse_gain": 2000, # [DAC units]
            "pulse_freq": {"freq": 1000, "gen_ch":0, "ro_ch":0}, # [MHz]
            }
            self.freqB = {
            "res_phase": 90 , # The phase of the signal
            "pulse_gain": 2000, # [DAC units]
            "pulse_freq": {"freq": 1000, "gen_ch":0, "ro_ch":0}, # [MHz]
            }
            A = "freqA"
            B = "freqB"
            self.configEOM={"out_ch":[0,1],
                    "freq_seq": [A,B,A,B],
                    "time_seq":[50, 190,370,700],
                    "length":100, # [Clock ticks]
                    "pulse_freq":{"freq":1000, "gen_ch":0, "ro_ch":0}, #readout freq
                    "zone": 1,
                    "mode": "periodic",
            }

            #TTL
            self.configAOM={
                    "length":[[200,200,200,200],[200,200,200,200],[200,200,200,200],[200,200,200,200]], # [Clock ticks]
                    "pins":[1,2,0,3],
                    "time":[[0,400,800,1200],[0,400,800,1200],[0,400,800,1200],[0,400,800,1200]],
            }
            self.configG= {
            "adc_trig_offset": 100, # [Clock ticks]
            "soft_avgs":1,
            "relax_delay":1.0, # --us
            #Readout
            "readout_length": 2000, # [Clock ticks]
            "pulse_freq":{"freq":1000, "gen_ch":0, "ro_ch":0},
            "reps":1, # --Fixed
            }
            file_name = "config_file.py"
            file_content ='''
from qick import *
from qick.parser import load_program
# Load bitstream with custom overlay
soc = QickSoc()

soccfg = soc
freqA = {"res_phase": '''+str(self.freqA["res_phase"])+''' , # The phase of the signal
        "pulse_gain": '''+str(self.freqA["pulse_gain"])+''', # [DAC units]
        "pulse_freq": soccfg.adcfreq('''+str(self.freqA["pulse_freq"]["freq"])+''', gen_ch='''+str(self.freqA["pulse_freq"]["gen_ch"])+''', ro_ch='''+str(self.freqA["pulse_freq"]["ro_ch"])+'''), # [MHz]
        }
freqB = {"res_phase": '''+str(self.freqB["res_phase"])+''' , # The phase of the signal
        "pulse_gain": '''+str(self.freqB["pulse_gain"])+''', # [DAC units]
        "pulse_freq": soccfg.adcfreq('''+str(self.freqB["pulse_freq"]["freq"])+''', gen_ch='''+str(self.freqB["pulse_freq"]["gen_ch"])+''', ro_ch='''+str(self.freqB["pulse_freq"]["ro_ch"])+'''), # [MHz]
        }
configEOM={"out_ch":'''+str(self.configEOM["out_ch"])+''',
        "freqA": freqA,
        "freqB": freqB,
        "freq_seq": '''+str(self.configEOM["freq_seq"])+''',
        "time_seq":'''+str(self.configEOM["time_seq"])+''',
        "length":'''+str(self.configEOM["length"])+''', # [Clock ticks]
        "pulse_freq":soccfg.adcfreq('''+str(self.configEOM["pulse_freq"]["freq"])+''', gen_ch='''+str(self.configEOM["pulse_freq"]["gen_ch"])+''', ro_ch='''+str(self.configEOM["pulse_freq"]["ro_ch"])+'''), # [MHz]
        "zone": '''+str(self.configEOM["zone"])+''',
        "mode": "'''+str(self.configEOM["mode"])+'''",
}

#TTL
configAOM={
        "length":'''+str(self.configAOM["length"])+''', # [Clock ticks]
        "pins":'''+str(self.configAOM["pins"])+''',
        "time":'''+str(self.configAOM["time"])+''',
}
config= {
"adc_trig_offset": '''+str(self.configG["adc_trig_offset"])+''', # [Clock ticks]
"soft_avgs":'''+str(self.configG["soft_avgs"])+''',
"relax_delay":'''+str(self.configG["relax_delay"])+''', # --us
#Readout
"readout_length": '''+str(self.configG["readout_length"])+''', # [Clock ticks]
"pulse_freq":soccfg.adcfreq('''+str(self.configG["pulse_freq"]["freq"])+''', gen_ch='''+str(self.configG["pulse_freq"]["gen_ch"])+''', ro_ch='''+str(self.configG["pulse_freq"]["ro_ch"])+'''),
"reps":'''+str(self.configG["reps"])+''', # --Fixed
"EOM":configEOM,
"AOM":configAOM
}

from XMLGenerator import dict_to_xml_file,xml_config_to_dict
dict_to_xml_file(config, "xilinx.xml")
'''

            # Open the file in write mode and write the content
            with open(file_name, "w") as file:
                    file.write(file_content)

            self.RFSoC.transfer_file(r"config_file.py",r"/home/xilinx/jupyter_notebooks/qick/qick_demos/ssh_control/config_file.py")
            self.RFSoC.run_code("config_file")
            self.RFSoC.download_file(r"/home/xilinx/jupyter_notebooks/qick/qick_demos/ssh_control/xilinx.xml",r"xilinx.xml")

    def run_code(self):
        self.build_config()
        self.RFSoC.transfer_file(r"config_file.py",r"/home/xilinx/jupyter_notebooks/qick/qick_demos/ssh_control/config_file.py")
        self.RFSoC.run_code("RFSoC")

    def get_config(self,print=False):
        file_path = "xilinx.xml"  # Replace with the actual file path

        if not os.path.exists(file_path):
            try:
                self.RFSoC.download_file(r"/home/xilinx/jupyter_notebooks/qick/qick_demos/ssh_control/config.xml",r"config.xml")
            except Exception as e:
                return False
        try:
            self.config = xml_config_to_dict(file_path)
            if print:
                print(self.config)
                return True

        except Exception as e:
            return False

    def set_config(self, category, value, key): #EXCEPT FREQUENCY FOR EOM ONLY FOR TTL AND GENERAL EOM AND AOM
        if category == "G":
            try:
                self.config[value] = key
            except Exception as e:
                # Exception handling code
                print(f"An error occurred: {str(e)}")
        elif category == "EOM":
            try:
                self.configEOM[value] = key
            except Exception as e:
                # Exception handling code
                print(f"An error occurred: {str(e)}")
        elif category == "AOM":
            try:
                self.configAOM[value] = key
            except Exception as e:
                # Exception handling code
                print(f"An error occurred: {str(e)}")
        elif category == "freqA":
            try:
                self.freqA[value] = key
            except Exception as e:
                # Exception handling code
                print(f"An error occurred: {str(e)}")
        elif category == "freqB":
            try:
                self.freqB[value] = key
            except Exception as e:
                # Exception handling code
                print(f"An error occurred: {str(e)}")
        return "Configuration set successfully"


# config_host = xml_config_to_dict("xilinx_host.xml")["database"]
# test = RFSoC_controller(config_host=config_host)
# test.run_code()