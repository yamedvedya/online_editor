# Created by matveyev at 07.04.2021

#!/usr/bin/python3

import io
import os
import sys
import datetime

from build import build_gui

REQUIRED = ['PyQt5', 'psutil']

build_gui()

# here = os.path.abspath(os.path.dirname(__file__))
# if sys.platform == "linux" or sys.platform == "linux2":
#     with open(os.path.expanduser("~/.bashrc"), "at") as bashrc:
#         bashrc.write(
#             "\n" + "# Added by OnlinexmlEditor on {}\n".format(datetime.date.today()) + "alias devices='cd ~/Desktop/'\n"
#         )

# elif sys.platform == "win32":
