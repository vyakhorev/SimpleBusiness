# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
from ui.ui_SimulWindow import Ui_MainSimulWindow
from gui_forms_logic.data_models_simul import gui_mainsim_varlist_model,\
    gui_testsim_varlist_model, gui_testsimlog_table_model

from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar

from c_planner import c_planner
import db_main

import random
import sys


class gui_MainSimulWindow(QtGui.QMainWindow, Ui_MainSimulWindow):

    def __init__(self, app, parent=None):
        super(gui_MainSimulWindow, self).__init__(parent)
        self.app = app
        self.setupUi(self)

        #self.connect(self.action_Run_Simulate, QtCore.SIGNAL("triggered()"), self.action_run_simulation)
        ##################################################################
        #Вкладка с графиками (Simulation)
        self.gui_models_mainsim_varlist = gui_mainsim_varlist_model()
        self.gui_models_mainsim_varlist_proxy = QtGui.QSortFilterProxyModel()
        self.gui_models_mainsim_varlist_proxy.setSourceModel(self.gui_models_mainsim_varlist)
        self.gui_models_mainsim_varlist_proxy.setDynamicSortFilter(True)
        self.gui_models_mainsim_varlist_proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

        self.listView_main_sim.setModel(self.gui_models_mainsim_varlist_proxy)
        self.connect(self.listView_main_sim.selectionModel(), QtCore.SIGNAL("currentChanged(QModelIndex, QModelIndex)"), self.build_simulation_reports)
        self.connect(self.lineEdit_find_var_mainsim, QtCore.SIGNAL("textChanged(QString)"), self.gui_models_mainsim_varlist_proxy.setFilterRegExp)
        self.connect(self.button_zoom, QtCore.SIGNAL("clicked()"), self.zoom)
        self.connect(self.button_pan, QtCore.SIGNAL("clicked()"), self.pan)
        self.connect(self.button_home, QtCore.SIGNAL("clicked()"), self.home)
        self.connect(self.button_saveplot, QtCore.SIGNAL("clicked()"), self.palette)
        #Тулбарчик манипуляций над графиком
        self.toolbar = NavigationToolbar(self.SIM_INF_mpl_plot.figure.canvas, self)
        self.toolbar.hide()

        ##################################################################
        #Вкладка с тестовыми симуляциями (Log)
        self.gui_models_testsim_varlist = gui_testsim_varlist_model()
        self.gui_models_testsim_varlist_proxy = QtGui.QSortFilterProxyModel()
        self.gui_models_testsim_varlist_proxy.setSourceModel(self.gui_models_testsim_varlist)
        self.gui_models_testsim_varlist_proxy.setDynamicSortFilter(True)
        self.gui_models_testsim_varlist_proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

        self.gui_models_testsimlog_table = gui_testsimlog_table_model()
        self.gui_models_testsimlog_table_proxy = QtGui.QSortFilterProxyModel()
        self.gui_models_testsimlog_table_proxy.setSourceModel(self.gui_models_testsimlog_table)
        self.gui_models_testsimlog_table_proxy.setDynamicSortFilter(True)
        self.gui_models_testsimlog_table_proxy.setFilterKeyColumn(1)
        self.gui_models_testsimlog_table_proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

        self.connect(self.button_log_run_simul, QtCore.SIGNAL("clicked()"), self.run_test_simulation_selected_seed)
        self.connect(self.pushButton_log_run_simul_random, QtCore.SIGNAL("clicked()"), self.run_test_simulation_random_seed)
        self.log_table_browser.setModel(self.gui_models_testsimlog_table_proxy)
        self.listView_log_var_list.setModel(self.gui_models_testsim_varlist_proxy)
        self.connect(self.lineEdit_SearchInLog, QtCore.SIGNAL("textChanged(QString)"), self.gui_models_testsimlog_table_proxy.setFilterRegExp)
        self.connect(self.lineEdit_testsim_findvar, QtCore.SIGNAL("textChanged(QString)"), self.gui_models_testsim_varlist_proxy.setFilterRegExp)
        self.connect(self.listView_log_var_list.selectionModel(), QtCore.SIGNAL("currentChanged(QModelIndex, QModelIndex)"), self.log_show_a_variable)
        ##################################################################
        self.startUi()

    def update_ui_tab_change(self, tab_num):
        #При смене вкладки обновляем содержимое
        tab_wid = self.Global_tabs.widget(tab_num)
        if tab_wid:
            if tab_wid.objectName() == "tab_Simulation":      #Simulation
                self.gui_models_mainsim_varlist.update_with_observations()
            elif tab_wid.objectName() == "tab_SimulLog":      #Log
                self.update_log_lists()

    def startUi(self):
        self.update_log_lists()

    def action_run_simulation(self):
        the_planner = c_planner()
        param_dict = db_main.the_settings_manager.get_simul_settings()
        the_planner.run_observed_simulation(param_dict["epoch_num"], param_dict["until"])
        self.gui_models_mainsim_varlist.update_with_observations()
        self.update_log_lists()

    def build_simulation_reports(self, index_to, index_from):
        #Строим HTML-отчет
        report = index_to.data(35).toPyObject()
        self.textBrowser_Simulation.setHtml(report.get_html())
        self.plotter(report.get_dataframe_to_plot(), report.get_name())

    def zoom(self):
        self.toolbar.zoom()

    def pan(self):
        self.toolbar.pan()

    def home(self):
        self.toolbar.home()

    def palette(self):
        self.toolbar.save_figure()

    def plotter(self, dframe, legend,title='', clear=True, dots_form='-'):
        #TODO: а что тут с памятью?...
        if clear == True:
            self.SIM_INF_mpl_plot.figure.clear()
        ax = self.SIM_INF_mpl_plot.figure.add_subplot(111)
        ax.plot(dframe, dots_form)
        ax.figure.suptitle(title)
        if legend <> "":
            ax.legend(legend, loc='best')
        ax.figure.canvas.draw()
        def onclick(event):  #Это как-то очень заумно
            print 'button=%d, x=%d, y=%d, xdata=%f, ydata=%f'%(
            event.button, event.x, event.y, event.xdata, event.ydata)
        #cid = ax.figure.canvas.mpl_connect('button_press_event', onclick)

    def run_test_simulation_selected_seed(self):
        a_seed = self.seed_cmbx.itemData(self.seed_cmbx.currentIndex(),32).toPyObject()
        self.run_test_simulation(a_seed)

    def run_test_simulation_random_seed(self):
        a_seed = random.randint(0, sys.maxint)
        self.run_test_simulation(a_seed)

    def run_test_simulation(self, test_seed):
        the_planner = c_planner()
        log_dict = the_planner.run_and_return_log(test_seed)
        # Обновим табличку с логами
        start_date = db_main.the_settings_manager.get_param_value("initial_data_date")
        self.gui_models_testsimlog_table.update_logs(start_date, log_dict["log_list"])
        # Обновим список переменных
        sim_results = log_dict["sim_results"]  #Сложно...
        self.gui_models_testsim_varlist.update_with_observations(sim_results)

    def update_log_lists(self):
        self.seed_cmbx.clear()
        for ep_i in db_main.iter_epoch_data():
            self.seed_cmbx.addItem("epoch #" +str(ep_i.epoh_num) + " seed #" +str(ep_i.seed_value), ep_i.seed_value)

    def log_show_a_variable(self, index_to, index_from):
        data = index_to.data(35).toPyObject()
        if data is not None:
            [obs_name, pd_dataframe] = data
            #TODO: а что тут с памятью?...
            self.mplwidget_testsim.figure.clear()
            ax = self.mplwidget_testsim.figure.add_subplot(111)
            ax.plot(pd_dataframe, "-")
            ax.figure.suptitle(unicode(obs_name))
            ax.figure.canvas.draw()

