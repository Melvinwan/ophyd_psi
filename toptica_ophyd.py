import functools
import threading
import time
from typing import List
import abc
import typing
import logging
from ophyd.log import config_ophyd_logging
# config_ophyd_logging(file='/tmp/ophyd.log', level='DEBUG')
from prettytable import PrettyTable
from log_ophyd import log_ophyd

import numpy as np
# from bec_utils import BECMessage, MessageEndpoints, bec_logger
from ophyd import Component as Cpt
from ophyd import Device, PositionerBase, Signal
from ophyd.status import wait as status_wait
from ophyd.utils import LimitError, ReadOnlyError

from ophyd.ophydobj import OphydObject

# import asyncio
from IPython.display import clear_output
from toptica.lasersdk.client import Client, NetworkConnection, DeviceNotFoundError
from toptica.lasersdk.client import UserLevel, Subscription, Timestamp, SubscriptionValue
from toptica.lasersdk.dlcpro.v2_0_3 import DLCpro, NetworkConnection, DeviceNotFoundError, DecopError, UserLevel

logger = log_ophyd("laser_log.txt",__name__)

DEFAULT_EPICSSIGNAL_VALUE = object()
class LaserCommunicationError(Exception):
    pass


class LaserError(Exception):
    pass


# def retry_once(fcn):
#     """Decorator to rerun a function in case a Laser communication error was raised. This may happen if the buffer was not empty."""

#     @functools.wraps(fcn)
#     def wrapper(self, *args, **kwargs):
#         try:
#             val = fcn(self, *args, **kwargs)
#         except (LaserCommunicationError, LaserError):
#             val = fcn(self, *args, **kwargs)
#         return val

#     return wrapper

# def threadlocked(fcn):
#     """Ensure that the thread acquires and releases the lock."""

#     @functools.wraps(fcn)
#     def wrapper(self, *args, **kwargs):
#         lock = self._lock if hasattr(self, "_lock") else self.dlc._lock
#         with lock:
#             return fcn(self, *args, **kwargs)

#     return wrapper

_type_map = {
    "number": (float, np.floating),
    "array": (np.ndarray, list, tuple),
    "string": (str,),
    "integer": (int, np.integer),
}

def data_shape(val):
    """Determine data-shape (dimensions)

    Returns
    -------
    list
        Empty list if val is number or string, otherwise
        ``list(np.ndarray.shape)``
    """
    if data_type(val) != "array":
        return []

    try:
        return list(val.shape)
    except AttributeError:
        return [len(val)]


def data_type(val):
    """Determine the JSON-friendly type name given a value

    Returns
    -------
    str
        One of {'number', 'integer', 'array', 'string'}

    Raises
    ------
    ValueError if the type is not recognized
    """
    bad_iterables = (str, bytes, dict)
    if isinstance(val, typing.Iterable) and not isinstance(val, bad_iterables):
        return "array"

    for json_type, py_types in _type_map.items():
        if isinstance(val, py_types):
            return json_type

    raise ValueError(
        f"Cannot determine the appropriate bluesky-friendly data type for "
        f"value {val} of Python type {type(val)}. "
        f"Supported types include: int, float, str, and iterables such as "
        f"list, tuple, np.ndarray, and so on."
    )

class LaserController(OphydObject): #On off laser similar to controller
    _controller_instances = {}
    _get_lists = ["laser1:ctl:wavelength-act", "laser1:scan:end","laser1:scan:frequency","laser1:scan:offset"]
    USER_ACCESS = [
        "set_laser","get_laser","off"
    ]
    SUB_CONNECTION_CHANGE = "connection_change"

    def __init__(
        self,
        *,
        name=None,
        host=None,
        port=None,
        attr_name="",
        parent=None,
        labels=None,
        kind=None,
    ):
        if not hasattr(self, "_initialized"):
            super().__init__(
                name=name, attr_name=attr_name, parent=parent, labels=labels, kind=kind
            )

            self._lock = threading.RLock()
            self.host = host
            self.port = port
            self._initialized = True
            self._initialize()

    def _initialize(self):
        # self._connected = False
        print(f"connecting to {self.host}")
        logger.info("The connection has already been established.")
        self.dlc = DLCpro(NetworkConnection(self.host))
        self.dlc.open()
        # self.name = "self.dlc.system_model.get()+self.dlc.system_type.get()+ self.dlc.serial_number.get()"
        self._connected = True
        self._set_default_values()
        self.name = "DLCPro"
        self.is_open = True

    def _set_default_values(self):
        # no. of axes controlled by each controller
        self._wavelength_act = 1550
        self._scan_end = 75
        self._scan_start = 50
        self._scan_freq = 10
        self._scan_offset = 70
        # self._wide_scan_amplitude = 120
        # self._wide_scan_offset = 1570

    @property
    def connected(self):
        return self._connected

    # def connect(self):
    #     print(f"connecting to {self.host}")
    #     self.dlc = DLCpro(NetworkConnection(self.host)).open()
    #     # self.name = "self.dlc.system_model.get()+self.dlc.system_type.get()+ self.dlc.serial_number.get()"
    #     self._connected = True
    # def open(self):
    #     self.connect()
    #     self.is_open = True

    # def start_wide_scan(self):
    #     if not self.connected:
    #         print("The connection has not been established")
    #     else:
    #         self.dlc.laser1.wide_scan.start.exec()
    # def stop_wide_scan(self):
    #     if not self.connected:
    #         print("The connection has not been established")
    #     else:
    #         self.dlc.laser1.wide_scan.stop.exec()


    def off(self):
        """Close the connection to the laser"""
        logger.info("The connection is already closed.")
        self.dlc.close()
        self.connected = False

    def get_laser_data(self):
        signals = {
            # "wide scan amplitude":{"value": self.dlc.laser1.wide_scan.amplitude.get()},
            # "wide scan offset":{"value": self.dlc.laser1.wide_scan.offset.get()},
            # "wide scan remaining time":{"value": self.dlc.laser1.wide_scan.remaining_time.get()},
            "main scan end":{"value": self.dlc.laser1.scan.end.get()},
            "main scan start":{"value": self.dlc.laser1.scan.start.get()},
            "main scan frequency":{"value": self.dlc.laser1.scan.frequency.get()},
            "main scan offset":{"value": self.dlc.laser1.scan.offset.get()},
            "ctl wavelength":{"value":self.dlc.laser1.ctl.wavelength_act.get()}
        }
        return signals

    # def widescan_amplitude(self):
    #     return self.dlc.laser1.wide_scan.amplitude.get()

    # # @widescan_amplitude.setter
    # def widescan_amplitude_setter(self,val):
    #     self.dlc.laser1.wide_scan.amplitude.set(val)

    # def widescan_offset(self):
    #     return self.dlc.laser1.wide_scan.offset.get()

    # # @widescan_offset.setter
    # def widescan_offset_setter(self,val):
    #     self.dlc.laser1.wide_scan.offset.set(val)

    # def widescan_remaining_time(self):
    #     return self.dlc.laser1.wide_scan.remaining_time.get()

    def scan_end(self):
        logger.debug(f"recv scan end")
        return self.dlc.laser1.scan.end.get()

    # @scan_end.setter
    def scan_end_setter(self,val):
        logger.debug(f"set scan end")
        self.dlc.laser1.scan.end.set(val)
    def scan_start(self):
        logger.debug(f"recv scan start")
        return self.dlc.laser1.scan.start.get()

    # @scan_start.setter
    def scan_start_setter(self,val):
        logger.debug(f"set scan start")
        self.dlc.laser1.scan.start.set(val)
    def scan_frequency(self):
        logger.debug(f"recv scan frequency")
        return self.dlc.laser1.scan.frequency.get()

    # @scan_frequency.setter
    def scan_frequency_setter(self,val):
        logger.debug(f"set scan frequency")
        self.dlc.laser1.scan.frequency.set(val)

    def scan_offset(self):
        logger.debug(f"recv scan offset")
        return self.dlc.laser1.scan.offset.get()

    # @scan_offset.setter
    def scan_offset_setter(self,val):
        logger.debug(f"set scan offset")
        self.dlc.laser1.scan.offset.set(val)

    def wavelength_act(self):
        logger.debug(f"recv wavelength act")
        return self.dlc.laser1.ctl.wavelength_act.get()

    # @wavelength_act.setter
    def wavelength_act_setter(self,val):
        logger.debug(f"set wavelength act")
        self.dlc.laser1.ctl.wavelength_set.set(val)

    def describe(self) -> None:
        t = PrettyTable()
        t.title = f"{self.__class__.__name__} on {self.sock.host}:{self.sock.port}"
        t.field_names = [
            # "wide scan amplitude",
            # "wide scan offset",
            # "wide scan remaining time",
            "main scan end",
            "main scan start",
            "main scan frequency",
            "main scan offset",
            "wavelength act"
        ]
        t.add_row(
                    [
                        # self.widescan_amplitude(),
                        # self.widescan_offset(),
                        # self.widescan_remaining_time(),
                        self.scan_end(),
                        self.scan_start(),
                        self.scan_frequency(),
                        self.scan_offset(),
                        self.wavelength_act()
                    ]
                )
        print(t)

    # def __new__(cls, *args, **kwargs):
    #     socket = kwargs.get("socket")
    #     if not hasattr(socket, "host"):
    #         raise RuntimeError("Socket must specify a host.")
    #     if not hasattr(socket, "port"):
    #         raise RuntimeError("Socket must specify a port.")
    #     host_port = f"{socket.host}:{socket.port}"
    #     if host_port not in Controller._controller_instances:
    #         Controller._controller_instances[host_port] = object.__new__(cls)
    #     return Controller._controller_instances[host_port]
class LaserSignalBase(abc.ABC,Signal): #Similar to socketsignal
    SUB_SETPOINT = "setpoint"
    def __init__(self, signal_name, **kwargs):
        self.signal_name = signal_name
        super().__init__(**kwargs)
        self.dlc = self.parent.lasercontroller

    @abc.abstractmethod
    def _get(self):
        ...

    @abc.abstractmethod
    def _set(self, val):
        ...

    def get(self):
        self._readback = self._get()
        return self._readback

    def put(self, value):
        """Set the motor instance for a specified controller axis."""
        self._set(value)
        timestamp = time.time()
        old_value = self.get()
        VALUE = value
        super().put(value, timestamp=timestamp,force=True)
        self._run_subs(sub_type=self.SUB_SETPOINT, old_value=old_value,
                       value=VALUE, timestamp=self.timestamp)
    def describe(self):
        if self._readback is DEFAULT_EPICSSIGNAL_VALUE:
            val = self.get()
        else:
            val = self._readback
        return {
            self.name: {
                "source":self.dlc.name,
                "dtype": data_type(val),
                "shape":data_shape(val)
            }
        }

    # def get_laser(self, item):
    #     """Get motor instance for a specified controller axis."""
    #     return self._client.get(item)

class LaserSignalRO(LaserSignalBase):
    def __init__(self, signal_name, **kwargs):
        super().__init__(signal_name, **kwargs)
        self._metadata["write_access"] = False

    # @threadlocked
    def _set(self):
        raise ReadOnlyError("Read-only signals cannot be set")

# class LaserWideScanAmplitude(LaserSignalBase):
#     # @threadlocked
#     def _get(self):
#         return self.dlc.widescan_amplitude()

#     # @threadlocked
#     def _set(self, val):
#         self.dlc.widescan_amplitude_setter(val)

# class LaserWideScanOffset(LaserSignalBase):
#     # @threadlocked
#     def _get(self):
#         return self.dlc.widescan_offset()

#     # @threadlocked
#     def _set(self, val):
#         self.dlc.widescan_offset_setter(val)

# class LaserWideScanRemainingTime(LaserSignalRO):
#     # @threadlocked
#     def _get(self):
#         return self.dlc.widescan_remaining_time()

class LaserMainScanEnd(LaserSignalBase):
    # @threadlocked
    def _get(self):
        return self.dlc.scan_end()

    # @threadlocked
    def _set(self, val):
        logger.info("Main Scan end is set to "+str(val))
        self.dlc.scan_end_setter(val)

class LaserMainScanStart(LaserSignalBase):
    # @threadlocked
    def _get(self):
        return self.dlc.scan_start()

    # @threadlocked
    def _set(self, val):
        logger.info("Main Scan start is set to "+str(val))
        self.dlc.scan_start_setter(val)

class LaserMainScanFrequency(LaserSignalBase):
    # @threadlocked
    def _get(self):
        return self.dlc.scan_frequency()

    # @threadlocked
    def _set(self, val):
        logger.info("Main Scan frequency is set to "+str(val))
        self.dlc.scan_frequency_setter(val)

class LaserMainScanOffset(LaserSignalBase):
    # @threadlocked
    def _get(self):
        return self.dlc.scan_offset()
    # @threadlocked
    def _set(self, val):
        logger.info("Main Scan offset is set to "+str(val))
        self.dlc.scan_offset_setter(val)

class LaserMainCtlWavelengthAct(LaserSignalBase):
    # @retry_once
    # @threadlocked
    def _get(self):
        return self.dlc.wavelength_act()
    # @threadlocked
    def _set(self, val):
        logger.info("Main ctl wavelength is set to "+str(val))
        self.dlc.wavelength_act_setter(val)


class LaserToptica(Device):
    # widescan_amplitude = Cpt(LaserWideScanAmplitude, signal_name="widescan_amplitude")
    # widescan_offset = Cpt(LaserWideScanOffset, signal_name="widescan_offset")
    # widescan_time = Cpt(LaserWideScanRemainingTime, signal_name="widescan_remaining_time")
    scan_end = Cpt(LaserMainScanEnd, signal_name="scan_end")
    scan_start = Cpt(LaserMainScanStart, signal_name="scan_start")
    scan_offset = Cpt(LaserMainScanOffset, signal_name="scan_offset")
    scan_frequency =Cpt(LaserMainScanFrequency, signal_name="scan_frequency")
    ctl_wavelength_act = Cpt(LaserMainCtlWavelengthAct, signal_name="wavelength_act")
    low_limit_wavelength = Cpt(Signal, value=1510, kind="omitted")

    def __init__(self, prefix,name, host, port=None, kind=None,configuration_attrs=None, parent=None,**kwargs):
        self.lasercontroller = LaserController(host=host,port=port)
        super().__init__(
            prefix=prefix,
            name=name,
            kind=kind,
            # read_attrs=read_attrs,
            configuration_attrs=configuration_attrs,
            parent=parent,
            **kwargs,
        )
        self.name = name
        self.tolerance = kwargs.pop("tolerance", 0.5)
        self.scan_end.kind = "hinted"
        self.scan_start.kind = "hinted"
        self.scan_offset.kind = "hinted"
        self.scan_frequency.kind = "hinted"
        self.ctl_wavelength_act.kind = "hinted"

    # def update_widescan_amplitude(self,val):
    #     self.widescan_amplitude.put(val)
    # def update_widescan_offset(self,val):
    #     self.widescan_offset.put(val)
    # def update_widescan_time(self,val):
    #     self.widescan_time.put(val)
    def limit_wavelength(self):
        return self.low_limit_wavelength.get()
    def update_scan_end(self,val):
        self.scan_end.put(val)
    def update_scan_start(self,val):
        self.scan_start.put(val)
    def update_scan_offset(self,val):
        self.scan_offset.put(val)
    def update_scan_offset(self,val):
        self.scan_frequency.put(val)
    def update_ctl_wavelength_act(self,val):
        self.ctl_wavelength_act.put(val)
    # def report_widescan_amplitude(self,val):
    #     return self.widescan_amplitude.get()
    # def report_widescan_offset(self,val):
    #     return self.widescan_offset.get()
    # def report_widescan_time(self,val):
    #     return self.widescan_time.get()
    def report_scan_end(self):
        return self.scan_end.get()
    def report_scan_start(self):
        return self.scan_start.get()
    def report_scan_offset(self):
        return self.scan_offset.get()
    def report_scan_frequency(self):
        return self.scan_frequency.get()
    def report_ctl_wavelength_act(self):
        return self.ctl_wavelength_act.get()

    def stage(self) -> List[object]:
        return super().stage()

    def unstage(self) -> List[object]:
        return super().unstage()

    def stop(self, *, success=False):
        self.controller.stop_all_axes()
        return super().stop(success=success)


if __name__ == "__main__":
    LTDLC = LaserToptica(prefix="...",name="LTDLC", host="129.129.98.110")
    LTDLC.stage()
    print(LTDLC.read())

    # print(LTDLC.get())
    # print(LTDLC.describe())

    LTDLC.unstage()
