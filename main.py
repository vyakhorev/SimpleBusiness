# -*- coding: utf-8 -*-

"""
Created on Wed Mar 20 10:12:03 2013

@author: Vyakhorev, Dozdikov

Calls:
python main.py
python main.py -gui crm
- CRM-interface
python main.py -gui simul
- Simulation interface
python main.py -gui data
- Data browser interface (to ensure everything is loaded)
python main.py -gui nogui -action simul
- Perform simulations
python main.py -gui nogui -action load
- Load everything from 1C (from xml file)


"""

import sys
import argparse

# GUI varaints

def run_crm_gui():
    from main_gui_modern import QtGui, gui_MainWindow
    app = QtGui.QApplication(sys.argv)
    #Start interacting with user
    form = gui_MainWindow(app)
    form.show()
    app.exec_()

def run_simul_gui():
    from main_gui_simul import QtGui, gui_MainSimulWindow
    app = QtGui.QApplication(sys.argv)
    #Start interacting with user
    form = gui_MainSimulWindow(app)
    form.show()
    app.exec_()

def run_data_gui():
    from main_gui_datacheck import QtGui, gui_MainDataWindow
    app = QtGui.QApplication(sys.argv)
    #Start interacting with user
    form = gui_MainDataWindow(app)
    form.show()
    app.exec_()

# Scripts

def run_simulations():
    from c_planner import c_planner
    import db_main
    the_planner = c_planner()
    param_dict = db_main.the_settings_manager.get_simul_settings()
    the_planner.run_observed_simulation(10, 200)

def load_from_1C():
    import admin_scripts
    mng = admin_scripts.c_admin_tasks_manager()
    mng.add_task(admin_scripts.c_read_lists_from_1C_task())
    mng.add_task(admin_scripts.c_read_logs_from_1C_task())
    mng.add_task(admin_scripts.c_read_dynamic_data_from_1C_task())
    mng.add_task(admin_scripts.c_read_generalinfo_from_1C_task())
    mng.add_task(admin_scripts.c_update_ccy_stats())
    mng.add_task(admin_scripts.c_build_excessive_links())
    mng.run_tasks()

if __name__ == "__main__":
    import simple_locale
    reload(sys)
    sys.setdefaultencoding(simple_locale.ultimate_encoding)

    parser = argparse.ArgumentParser(description='Run one of the processes for SimpleBusiness')
    parser.add_argument('-gui', dest='gui', choices=['crm', 'simul', 'data', 'nogui'])
    parser.add_argument('-action', dest='action', choices=['simul', 'load'])
    cmd_options = parser.parse_args()

    if cmd_options.gui is None:
        run_crm_gui()
    elif cmd_options.gui == 'crm':
        run_crm_gui()
    elif cmd_options.gui == 'simul':
        run_simul_gui()
    elif cmd_options.gui == 'data':
        run_data_gui()
    elif cmd_options.gui == 'nogui':
        # Этот вызов означает запуск скрипта
        if cmd_options.action == 'simul':
            run_simulations()
        elif cmd_options.action == 'load':
            load_from_1C()

