# -*- coding: utf-8 -*-

"""
Created on Wed Mar 20 10:12:03 2013

@author: Vyakhorev, Dozdikov
"""

import sys

if __name__ == "__main__":
    from main_gui_modern import *
    import simple_locale
    reload(sys)
    sys.setdefaultencoding(simple_locale.ultimate_encoding)
    app = QtGui.QApplication(sys.argv)
    #Start interacting with user
    form = gui_MainWindow(app)
    form.show()
    app.exec_()
