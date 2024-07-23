"""Connectivity package for D-Tacq uuts

**comprised of** :
    * acq400.py : Acq400 class, represents an ACQ400 UUT
    * acq400_ui.py : common user interface elements for apps
    * netclient.py : Netclient class, TCP socket wrapper
    * shotcontrol.py : Shotcontrol class, handles transient shots
    * acq400_print.py : cmd line interface functions
    * agilent33210.py : SCPI cmd wrapper
    * cleanup.py : cleanup on exit
    * rad_dds.py : support for RADCELF triple DDS

"""
import sys

from .netclient import Netclient
from .netclient import Siteclient
from .netclient import Logclient
from .acq400 import Acq400, STATE, AcqPorts, ChannelClient, MgtDramPullClient, sigsel, factory, Mgt508
from .acq400 import freq, freqpv, intpv, pv, activepv, floatpv
from .acq400 import Acq2106
from .acq400 import Acq2106_Mgtdram8
from .acq400 import Acq2106_TIGA
if sys.version_info > (3, 0):
    from .rad_dds import RAD3DDS
    from .rad_dds import AD9854
from .shotcontrol import *
from . import cleanup
from . import awg_data
from .acq400_ui import Acq400UI
from .acq400_print import PR, pprint
from .intSI import *
from .debug import Debugger
from .utils import timing
from .afhba404 import *
from .agilent33210 import Agilent33210A
from .propellor import *
from .acq400_logger import acq400_logger

from .version import get_version


