#-*- coding: utf-8 -*-

import sys
from PyQt4 import QtCore, QtGui

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import matplotlib.dates as mdates
from matplotlib import rc

rc('font', **{'family':'verdana'})
rc('text.latex', unicode=True)
rc('text.latex', preamble='\usepackage[utf8]{inputenc}')
rc('text.latex', preamble='\usepackage[russian]{babel}')

from datetime import datetime, timedelta
from itertools import cycle

import numpy as np
from scipy.stats import norm
import math

HD = [1280, 720]
COLORS = cycle(['r', 'g', 'b'])
COLORS_SEC = ['violet', 'm', 'darkviolet', 'r', 'orange']
LightGreen = [val/256. for val in [171, 205, 170]]

class DataPoint(object):
    def __init__(self, x, y):
        self.time = x
        self.val = y
        self.time_dev = Spreading([1, 1.5, 2])
        self.val_dev = Spreading([2, 2.5, 3])

    def __repr__(self):
        return 'DataPoint time : {} with spread {}, value : {} with spread {}'.format(self.time, self.time_dev,
                                                                               self.val,  self.val_dev)


class Spreading(object):
    """
        :param deltas - list of delta [d1,d2,...]
        :param maxprob - maximum probability
    """
    def __init__(self, deltas, maxprob=1.0):
        self.deltas = deltas
        self._sort_deltas = []
        self.maxprob = maxprob

    @property
    def sorted_deltas(self):
        """ deltas from small to big radius """
        self._sort_deltas = sorted(self.deltas, reverse=True)
        return self._sort_deltas

    def max(self):
        return max(self.deltas)

    def add_pair(self, pair):
        self.deltas += pair

    def __repr__(self):
        return 'spread : {}'.format(self.deltas)


class PlotViewerDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(PlotViewerDialog, self).__init__(parent)
        self.main_layout = QtGui.QVBoxLayout()

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)

        self.toolBar = NavigationToolbar(self.canvas, self)
        # self.button = QtGui.QPushButton('Plot')

        self.setLayout(self.main_layout)
        self.layout().addWidget(self.toolBar)
        # self.layout().addWidget(self.button)

        self.main_layout.insertWidget(1, self.canvas)
        self.resize(*HD)

    @staticmethod
    def minmax(data):
        if isinstance(data[0], datetime):
            return min(data), max(data)
        else:
            return min(data), max(data)

    def plot(self, data, current_date=None):
        """
            :param data: dict | {'name_of_series1' : [dataset1],
                                 'name_of_series2' : [dataset2], ...}
                                where dataset could be numpy.array of 4xN size [ time_i val_i time_i_dev val_i_dev
                                                                                   ........
                                                                                 time_N val_N time_N_dev val_N_dev]
                                       time_i : datetime()
                                       val_i : int
                                       time_i_dev : Spread() or 0
                                       val_i_dev  : Spread() or 0

                                or list of DataPoint [DataPoint1, DataPoint2, DataPoint3]
                                where DataPoint1 should be datetime type
            :param current_date: datetime() | current time parameter
            :return: None
        """

        ax1 = self.figure.add_subplot(111)

        for name, points in data.iteritems():
            # unpacking series
            if isinstance(data.values()[0], np.ndarray):
                time, value, time_dev, value_dev = data.values()[0].T.tolist()
                # print data

            else:
                time, value = [pt.time for pt in points], [pt.val for pt in points]
                time_dev, value_dev = [pt.time_dev for pt in points], [pt.val_dev for pt in points]

            # converting days to date from current date
            time = [current_date + timedelta(days=ts) for ts in time]

            maxval = [n.max() for n in value_dev if isinstance(n, Spreading)]
            maxdate = [t.max() for t in time_dev if isinstance(t, Spreading)]

            # Calculating boundaries for data
            date_min, date_max = self.minmax(time)
            value_min, value_max = self.minmax(value)
            value_min = 0
            # summing up max values with max spreadings
            value_max = value_max+max(maxval)
            date_max = date_max + timedelta(max(maxdate))

            # setting up boundaries
            ax1.set_xlim(date_min-timedelta(30), date_max+timedelta(30))
            ax1.set_ylim(value_min, value_max+(value_max-value_min)/5.)

            ax1.grid()
            ax1.plot(time, value, 'o', color=next(COLORS), label=unicode(name))

            if current_date:
                ax1.axvline(current_date, linewidth=2, color='g', ymin=0, ymax=10)
                ax1.axvspan(xmin=date_min-timedelta(30), xmax=current_date, ymin=0, ymax=10, color=LightGreen)

            # making ellipses
            for t_i, val_i, t_dev_i, val_dev_i in zip(time, value, time_dev, value_dev):

                # multiple concentric ellipses of spreading
                if t_dev_i > 0:
                    for i, (t_dev_ij, val_dev_ij) in enumerate(zip(t_dev_i.sorted_deltas, val_dev_i.sorted_deltas)):
                        if t_dev_ij > 0:
                            # print 'ellipse {} with width {} and height {}'.format(i, t_dev_ij, val_dev_ij)
                            ellip = Ellipse(xy=[t_i, val_i], width=t_dev_ij*2, height=val_dev_ij*2)
                            ellip.fill = True
                            ellip._alpha = t_dev_i.maxprob
                            ellip.set_color(COLORS_SEC[i])
                            ax1.add_artist(ellip)


        # ax1.format_coord = Formatter(data.values()[0])
        ax1.xaxis.set_major_locator(mdates.MonthLocator())
        ax1.xaxis.set_minor_locator(mdates.DayLocator(bymonthday=(1, 15)))
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %d %y'))

        self.figure.autofmt_xdate(bottom=0.2, rotation=35, ha='right')

        self.figure.tight_layout()
        ax1.legend(loc='best')
        self.canvas.draw()

def get_shipments_prediction_areas(Edt, Ev, Ddt, Dv, first_date, current_date, horiz):
    levels = [0.55]
    plevels = []
    for v in norm.ppf(levels):
        plevels += [v]

    ExpectationsT = []
    ExpectationsV = []
    SpreadingsT = []
    SpreadingsV = []

    sh = int(max((first_date - current_date).days, 0))

    if sh < horiz*2:
        horiz = horiz*2

    row_count = 0
    for t in xrange(sh, horiz, int(Edt)):
        row_count += 1
        # Calculate expectations
        #ND = current_date + timedelta(days=t)
        #ND.replace(hour=0, minute=0, second=0, microsecond=0)
        ExpectationsT += [t]
        ExpectationsV += [Ev]
        # Calculate area
        levels_T = []
        levels_V = []
        coef = math.sqrt(t)
        for v in plevels:
            levels_T += [v*Ddt*coef]
            levels_V += [v*Dv*coef]
        SpreadingsT += [Spreading(levels_T, maxprob=0.1)]
        SpreadingsV += [Spreading(levels_V, maxprob=0.1)]

    tmp_lst = []
    for r in range(0, row_count):
        tmp_lst.append([None, None, None, None])
    dataset_matrix = np.array(tmp_lst)

    dataset_matrix[:, 0] = ExpectationsT
    dataset_matrix[:, 1] = ExpectationsV
    dataset_matrix[:, 2] = SpreadingsT
    dataset_matrix[:, 3] = SpreadingsV

    #print(dataset_matrix)

    return dataset_matrix



class Formatter(object):
    """
        Capturing mouse position, not using atm
    """
    def __init__(self, info):
        self.info = info
        self.time, self.value, self.time_dev, self.value_dev = self.info.T.tolist()

    def __call__(self, x, y):
        # z = self.im.get_array()[int(y), int(x)]
        print(int(y), int(x))

        # print dates.num2date(x)
        return 'testing stuff'
        # return 'x={:.01f}, y={:.01f}, z={:.01f}'.format(x, y, z)

# testing
if __name__ == '__main__':
    qApp = QtGui.QApplication(sys.argv)

    data = {}
    data2 = {}
    dataset = [[1, 3], [2, 8], [3, 6], [4, 12], [5, 12]]
    # dataset2 = [[1, 5], [2, 10], [3, 8], [4, 11], [5, 12]]

    # matrix row : [time, val, time_dev, val_dev]
    deltas = Spreading([15, 20, 60])
    deltas2 = Spreading([1, 2, 3])

    dates = [datetime(2015, 8, 15), datetime(2015, 10, 2), datetime(2016, 2, 17), datetime(2016, 4, 20),
             datetime(2016, 6, 9)]

    dataset_matrix = np.array([[-112, 4,  0, 0],
                               [-93, 9,  0, 0],
                               [-84, 7,  deltas, deltas2],
                               [-55, 14, Spreading([15, 30, 60, 90], maxprob=0.1), Spreading([1, 2, 3, 4])],
                               [-36, 8,  deltas, deltas2],
                               [ 50, 31, Spreading([15, 30, 60], maxprob=0.5), Spreading([1, 2, 3]) ]])



    # dates = [datetime(2015, 10, 2), datetime(2016, 2, 17), datetime(2016, 4, 20)]
    #
    # dataset_matrix = np.array([[4, 7,  deltas, deltas2],
    #                            [5, 14, Spreading([15, 30, 60, 90], maxprob=0.1), Spreading([1, 2, 3, 4])],
    #                            [6, 8,  deltas, deltas2]])

    # overwriting 1 column to dates
    # dataset_matrix[:, 0] = dates
    print type(datetime(2015, 8, 15))

    data2['Lantorec'] = dataset_matrix
    # data['Lantor'] = [DataPoint(dataset[i][0], dataset[i][1]) for i in xrange(len(dataset))]
    # data['Unigel'] = [DataPoint(dataset2[i][0], dataset2[i][1]) for i in xrange(len(dataset))]

    wind = PlotViewerDialog()
    wind.plot(data2, current_date=datetime(2015, 12, 16))
    # wind.plot(data)
    wind.show()

    sys.exit(qApp.exec_())