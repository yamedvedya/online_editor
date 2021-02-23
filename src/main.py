# ----------------------------------------------------------------------
# Author:        yury.matveev@desy.de
# ----------------------------------------------------------------------


"""
"""

import sys
from optparse import OptionParser

from PyQt5 import QtWidgets

from src.mainwindow import MainWindow

# ----------------------------------------------------------------------
def main():
    parser = OptionParser()

    parser.add_option("-f", "--file", dest="file",
                      help="OnLine file")

    (options, _) = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)

    main_window = MainWindow(options)
    main_window.show()

    return app.exec_()


# ----------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main())
