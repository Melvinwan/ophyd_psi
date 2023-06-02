import functools
import threading
import time
from typing import List
from log_ophyd import log_ophyd

import numpy as np
from ophyd import Component as Cpt
from ophyd import Device, Signal
from ophyd.status import wait as status_wait
from ophyd.utils import LimitError, ReadOnlyError
from prettytable import PrettyTable

from sockets import SocketIO, SocketSignal
from controller import Controller, threadlocked

logger = log_ophyd("mag_log.txt",__name__)

class MagneticCommunicationError(Exception):
    pass

class MagneticError(Exception):
    pass

def retry_once(fcn):
    """Decorator to rerun a function in case a CommunicationError was raised. This may happen if the buffer was not empty."""

    @functools.wraps(fcn)
    def wrapper(self, *args, **kwargs):
        try:
            val = fcn(self, *args, **kwargs)
        except (MagneticCommunicationError, MagneticError):
            val = fcn(self, *args, **kwargs)
        return val

    return wrapper

class MagneticController(Controller):
    USER_ACCESS = [
        "describe",
        "show_running_threads",
        "magnetic_show_all",
        "socket_put_and_receive",
        "socket_put_confirmed",
    ]

    def __init__(
        self,
        *,
        name="MagneticController",
        kind=None,
        parent=None,
        socket=None,
        attr_name="",
        labels=None,
    ):
        if not hasattr(self, "_initialized") or not self._initialized:
            # self._Magnetic_axis_per_controller = 8
            # self._axis = [None for axis_num in range(self._galil_axis_per_controller)]
            super().__init__(
                name=name,
                socket=socket,
                attr_name=attr_name,
                parent=parent,
                labels=labels,
                kind=kind,
            )

    def on(self) -> None:
        """Open a new socket connection to the controller"""
        if not self.connected:
            self.sock.open()
            self.connected = True
        else:
            logger.info("The connection has already been established.")
            # warnings.warn(f"The connection has already been established.", stacklevel=2)

    def off(self) -> None:
        """Close the socket connection to the controller"""
        if self.connected:
            self.sock.close()
            self.connected = False
        else:
            logger.info("The connection is already closed.")

    def _remove_trailing_characters(self, var) -> str:
        if len(var) > 1:
            return var.split("\r\n")[0]
        return var

    @threadlocked
    def socket_put(self, val: str) -> None:
        self.sock.put(bytes(val, "ascii"))

    @threadlocked
    def socket_get(self) -> str:
        return self.sock.receive().decode("ascii").split(' ')

    @retry_once
    def socket_put_and_receive(self, val: str, remove_trailing_chars=False) -> str:
        self.socket_put(val)
        if remove_trailing_chars:
            return self._remove_trailing_characters(self.sock.receive().decode ("ascii").split(' ') [1])
        return self.socket_get()

    @retry_once
    def socket_put_confirmed(self, val: str) -> None:
        """Send message to controller and ensure that it is received by checking that the socket receives a colon.

        Args:
            val (str): Message that should be sent to the socket

        Raises:
            MagneticCommunicationError: Raised if the return value is not a colon.

        """
        return_val = self.socket_put_and_receive(val)
        if return_val != ":":
            raise MagneticCommunicationError(
                f"Expected return value of ':' but instead received {return_val}"
            )

    def get_current(self) -> str:
        current = self.socket_put_and_receive("GET_CURRENT\n")
        return current

    def set_field(self, val) -> None:
        logger.info("Field is set to "+str(val))
        self.socket_put("SET_FIELD +"+str(val)+"\n")

    def set_current(self, val) -> None:
        logger.info("Current is set to "+str(val))
        self.socket_put("SET_CURRENT +"+str(val)+"\n")

    def get_field(self) -> str:
        field = self.socket_put_and_receive("GET_FIELD\n")
        return field

    def get_voltage(self) -> str:
        voltage = self.socket_put_and_receive("GET_VOLTAGE\n")
        return voltage

    def get_adc_dac_temp(self) -> str:
        adc_dac_temp = self.socket_put_and_receive("GET_ADC_DAC_TEMP\n")
        return adc_dac_temp

    def get_box_temp(self) -> str:
        box_temp = self.socket_put_and_receive("GET_BOX_TEMP\n")
        return box_temp

    def get_rack_temp(self) -> str:
        rack_temp = self.socket_put_and_receive("GET_RACK_TEMP\n")
        return rack_temp

    def get_water_temp(self) -> str:
        water_temp = self.socket_put_and_receive("GET_WATER_TEMP\n")
        return water_temp

    def get_water_flow(self) -> str:
        water_flow = self.socket_put_and_receive("GET_WATER_FLOW\n")
        return water_flow

    # def show_running_threads(self) -> None:
    #     t = PrettyTable()
    #     t.title = f"Threads on {self.sock.host}:{self.sock.port}"
    #     t.field_names = [str(ax) for ax in range(self._galil_axis_per_controller)]
    #     t.add_row(
    #         [
    #             "active" if self.is_thread_active(t) else "inactive"
    #             for t in range(self._galil_axis_per_controller)
    #         ]
    #     )
    #     print(t)
    def describe(self) -> None:
        t = PrettyTable()
        t.title = f"{self.__class__.__name__} on {self.sock.host}:{self.sock.port}"
        t.field_names = [
            "Current",
            "Field",
            "Voltage",
            "Adc Dac Temp",
            "Box Temp",
            "Rack Temp",
            "Water Temp",
            "Water Flow"
        ]
        t.add_row(
                    [
                        self.get_current(),
                        self.get_field(),
                        self.get_voltage(),
                        self.get_adc_dac_temp(),
                        self.get_box_temp(),
                        self.get_rack_temp(),
                        self.get_water_temp(),
                        self.get_water_flow()
                    ]
                )
        print(t)

        # self.show_running_threads()

    def magnetic_show_all(self) -> None:
        for controller in self._controller_instances.values():
            if isinstance(controller, MagneticController):
                controller.describe()

class MagneticSignalBase(SocketSignal):
    def __init__(self, signal_name, **kwargs):
        self.signal_name = signal_name
        super().__init__(**kwargs)
        self.controller = self.parent.controller
        self.sock = self.parent.controller.sock


class MagneticSignalRO(MagneticSignalBase):
    def __init__(self, signal_name, **kwargs):
        super().__init__(signal_name, **kwargs)
        self._metadata["write_access"] = False

    def _socket_set(self, val):
        raise ReadOnlyError("Read-only signals cannot be set")

class MagneticField(MagneticSignalBase):
    def _socket_get(self) -> float:
        return float(self.controller.get_field()[1])

    @retry_once
    @threadlocked
    def _socket_set(self, val: float) -> None:
        self.controller.set_field(val)

class MagneticCurrent(MagneticSignalBase):
    def _socket_get(self) -> float:
        return float(self.controller.get_current()[1])

    @retry_once
    @threadlocked
    def _socket_set(self, val: float) -> None:
        self.controller.set_current(val)

class MagneticVoltage(MagneticSignalRO):
    @threadlocked
    def _socket_get(self):
        return float(self.controller.get_voltage()[1])

class MagneticADCDACTemp(MagneticSignalRO):
    @threadlocked
    def _socket_get(self):
        return float(self.controller.get_adc_dac_temp()[1])

class MagneticBoxTemp(MagneticSignalRO):
    @threadlocked
    def _socket_get(self):
        return float(self.controller.get_box_temp()[1])

class MagneticRackTemp(MagneticSignalRO):
    @threadlocked
    def _socket_get(self):
        return float(self.controller.get_rack_temp()[1])

class MagneticWaterTemp(MagneticSignalRO):
    @threadlocked
    def _socket_get(self):
        return float(self.controller.get_water_temp()[1])

class MagneticWaterFlow(MagneticSignalRO):
    @threadlocked
    def _socket_get(self):
        return float(self.controller.get_water_flow()[1])

class Magnetic(Device):
    USER_ACCESS = ["controller"]
    magnetic_current = Cpt(MagneticCurrent, signal_name = "Magnetic current",kind="hinted")
    magnetic_field = Cpt(MagneticField, signal_name = "Magnetic field",kind="hinted")
    magnetic_voltage = Cpt(MagneticVoltage, signal_name = "Magnetic voltage",kind="hinted")
    magnetic_ADCDAC_temp = Cpt(MagneticADCDACTemp, signal_name = "Magnetic ADCDAC temp",kind="hinted")
    magnetic_box_temp = Cpt(MagneticBoxTemp, signal_name = "Magnetic box temp",kind="hinted")
    magnetic_rack_temp = Cpt(MagneticRackTemp, signal_name = "Magnetic rack temp",kind="hinted")
    magnetic_water_temp = Cpt(MagneticWaterTemp, signal_name = "Magnetic water temp",kind="hinted")
    magnetic_water_flow = Cpt(MagneticWaterFlow, signal_name = "Magnetic water flow",kind="hinted")

    SUB_READBACK = "readback"
    SUB_CONNECTION_CHANGE = "connection_change"
    _default_sub = SUB_READBACK

    def __init__(
        self,
        prefix="",
        *,
        name,
        kind=None,
        read_attrs=None,
        configuration_attrs=None,
        parent=None,
        host="129.129.131.154",
        port=1234,
        sign=1,
        socket_cls=SocketIO,
        device_manager=None,
        limits=None,
        **kwargs,
    ):
        self.sign = sign
        self.controller = MagneticController(socket=socket_cls(host=host, port=port))
        self.controller.on()
        self.device_manager = device_manager
        super().__init__(
            prefix,
            name=name,
            kind=kind,
            read_attrs=read_attrs,
            configuration_attrs=configuration_attrs,
            parent=parent,
            **kwargs,
        )
        self.name = name
        self.controller.subscribe(
            self._update_connection_state, event_type=self.SUB_CONNECTION_CHANGE
        )
        self._update_connection_state()
        # self.readback.subscribe(self._forward_readback, event_type=self.readback.SUB_VALUE)

    def _update_connection_state(self, **kwargs):
        for walk in self.walk_signals():
            walk.item._metadata["connected"] = self.controller.connected

    def _forward_readback(self, **kwargs):
        kwargs.pop("sub_type")
        self._run_subs(sub_type="readback", **kwargs)

    @property
    def current(self):
        return self.magnetic_current.get()

    def current_setter(self, val):
        if isinstance(val, float):
            return self.magnetic_current.put(val)
    @property
    def field(self):
        return self.magnetic_field.get()

    def field_setter(self, val):
        if isinstance(val, float):
            return self.magnetic_field.put(val)

    @property
    def ADCDAC_temp(self):
        return self.magnetic_ADCDAC_temp.get()

    @property
    def box_temp(self):
        return self.magnetic_box_temp.get()

    @property
    def rack_temp(self):
        return self.magnetic_rack_temp.get()

    @property
    def water_temp(self):
        return self.magnetic_water_temp.get()
    @property
    def water_flow(self):
        return self.magnetic_water_flow.get()
    def stage(self) -> List[object]:
        return super().stage()

    def unstage(self) -> List[object]:
        return super().unstage()

    def stop(self, *, success=False):
        self.controller.stop_all_axes()
        return super().stop(success=success)


if __name__ == "__main__":
    magneticIR = Magnetic("H", name="magneticIR")
    # print(magneticIR.stage())

    print(magneticIR.read())

    # print(magneticIR.get())
    # print(magneticIR.describe())

    # magneticIR.unstage()

    # from sockets import SocketMock

    # magneticIR = Magnetic(
    #     "H", name="magneticIR", host="mpc2680.psi.ch", port=8081, socket_cls=SocketMock
    # )
    # magneticIR.stage()

    # magneticIR.controller.magnetic_show_all()
