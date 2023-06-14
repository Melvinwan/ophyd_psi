# Import the QICK drivers and auxiliary libraries
from qick import *
from qick.parser import load_program
from sequence import sequence_TTL
import numpy as np

from create_json import import_json_file, save_list_to_json_file

config = import_json_file("config.json")

# Load bitstream with custom overlay
soc = QickSoc()

soccfg = soc
out_chs = [0,1]

def divide_nested_list(nested_list, divisor):
    result = []
    for sublist in nested_list:
        divided_sublist = []
        for number in sublist:
            divided_sublist.append(round(number / divisor))
        result.append(divided_sublist)
    return result

class MultiSequenceProgram(AveragerProgram):
    def __init__(self,soccfg, cfg):
        super().__init__(soccfg, cfg)

    def initialize(self):
        cfg=self.cfg

        #EOM
        for ch in out_chs: #[0,1]
            #READOUT AT CHANNEL 0 and 1
            self.declare_readout(ch=ch, length=self.cfg["readout_length"],
                                 freq=self.cfg["EOM"]["pulse_freq"])

        idata = 30000*np.ones(16*cfg["EOM"]["length"])
#         qdata = 30000*np.ones(16*cfg["length"])

        for ch in self.cfg["EOM"]['out_ch']:
            #GENERATE AT CHANNEL 0 and 1
            self.declare_gen(ch=ch, nqz=cfg["EOM"]["zone"])
            #ADD PULSE AT CHANNEL 0 and 1
            self.add_pulse(ch=ch, name="measure", idata=idata)
#             self.add_pulse(ch=ch, name="measure", idata=idata,qdata=qdata)

        freq=soccfg.freq2reg(cfg["EOM"]["pulse_freq"])  # convert frequency to dac frequency
#         self.trigger(pins=[0], t=0) # send a pulse on pmod0_0, for scope trigger
        for ii, ch in enumerate(self.cfg["EOM"]['out_ch']):
            #PULSE REGISTER AT CHANNEL 0 and 1
            self.default_pulse_registers(ch=ch,style="arb",waveform="measure", mode=cfg["EOM"]["mode"])

    def body(self):
        cfg=self.cfg

        #EOM
        self.trigger(adcs=[0,1],adc_trig_offset=cfg["adc_trig_offset"])  # trigger the adc acquisition
        for ii, ch in enumerate(cfg["EOM"]['out_ch']):
            for jj,freq in enumerate(cfg["EOM"]["freq_seq"]):
                #PULSE REGISTER AT CHANNEL 0 and 1
                self.set_pulse_registers(ch=ch, freq=soccfg.freq2reg(cfg["EOM"][freq]["pulse_freq"]), phase=soccfg.deg2reg(cfg["EOM"][freq]["res_phase"]), gain=cfg["EOM"][freq]["pulse_gain"])
                #PULSE AT CHANNEL 0 and 1
                self.pulse(ch=ch, t=cfg["EOM"]["time_seq"][jj]) # play readout pulse

        #AOM
        self.cfg["AOM"]["time"] = divide_nested_list(self.cfg["AOM"]["time"],2.6)
        self.cfg["AOM"]["length"] = divide_nested_list(self.cfg["AOM"]["length"],2.6)

        time_list,length,pins_seq = sequence_TTL(self.cfg["AOM"]["time"], self.cfg["AOM"]["length"], self.cfg["AOM"]["pins"])
        for time_index, time in enumerate(time_list):
            self.trigger(adcs=self.ro_chs,
                    pins=pins_seq[time_index],
                    adc_trig_offset=self.cfg["adc_trig_offset"],
                     t = time,
                    width = length[time_index])
        self.wait_all()
        self.sync_all(self.us2cycles(self.cfg["relax_delay"]))

prog = MultiSequenceProgram(soccfg, config)

iq_list = prog.acquire_decimated(soc)
save_list_to_json_file(iq_list, "iq_list.json")