# -*- coding: utf-8 -*-
"""
Created on Mon Jun 23 10:27:50 2014

@author: hannes.maierflaig
"""
from guidata.qt.QtGui import QVBoxLayout, QMainWindow, QWidget, QComboBox, QGridLayout, QHBoxLayout, QFileDialog, QPushButton, QTextEdit
from guidata.qt.QtCore import SIGNAL

from guiqwt.curve import CurvePlot
from guiqwt.plot import CurveDialog
from guiqwt.builder import make

import numpy as np
import nptdms
import re

def plot( *items ):
    win = CurveDialog(edit=False, toolbar=True)
    plot = win.get_plot()
    for item in items:
        plot.add_item(item)
    win.show()
    win.exec_()

class plotWidget(QWidget):
    """
    Filter testing widget
    parent: parent widget (QWidget)
    x, y: NumPy arrays
    func: function object (the signal filter to be tested)
    """
    def __init__(self, parent, x, y, func):
        QWidget.__init__(self, parent)
        self.setMinimumSize(500, 500)
        self.x = x
        self.y = y
        self.func = func
        #---guiqwt related attributes:
        self.plot = None
        self.curve_item = None
        #---
        self.curveDialog = CurveDialog(edit=False,toolbar=True)
        self.curveDialog.get_itemlist_panel().show()
        
    def setup_widget(self, title):
        #---Create the plot widget:
        self.plot = self.curveDialog.get_plot()
        self.curve_item = make.curve([], [], color='b')
        self.plot.add_item(self.curve_item)
        self.plot.set_antialiasing(True)
        #---
        
        button = QPushButton(u"Test filter: %s" % title)
        self.connect(button, SIGNAL('clicked()'), self.process_data)
        button2 = QPushButton(u"Symmetrize Data")
        self.connect(button2, SIGNAL('clicked()'), self.symmetrizeData)
        buttonWidget = QWidget()        
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.curveDialog)
        vlayout = QVBoxLayout()
        buttonWidget.setLayout(vlayout)
        vlayout.addWidget(button)
        vlayout.addWidget(button2)
        vlayout.addStretch(1)
        hlayout.addWidget(buttonWidget)
        self.setLayout(hlayout)
        
        self.update_curve()
        
    def symmetrizeData(self):
        from lib.transportdata  import symmetrizeSignalUpDown, averageUpDownSweep
        newY = symmetrizeSignalUpDown(self.y,int(len(self.y)/2))
        print(len(self.y))
        newX = averageUpDownSweep(self.x)
#        np.linspace(min(self.x),max(self.x),len(self.y))
        newcurve = make.curve(newX,newY, color='r')
        self.plot.add_item(newcurve)
        
    def process_data(self):
        self.y = self.func(self.y)
        self.update_curve()
        
    def update_curve(self):
        #---Update curve
        self.curve_item.set_data(self.x, self.y)
        self.curve_item.plot().replot()
        self.plot.do_autoscale()
        #---


class previewTransportDataWindow(QWidget):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowTitle("previewTransportData")

        #Initialize Layout    
        layout = QGridLayout()
        layout.setVerticalSpacing(0)
        self.setLayout(layout)
        self.fileTextWindow = QTextEdit()
        self.fileTextWindow.setMaximumWidth(750)
        self.fileTextWindow.setMaximumHeight(50)
        self.groupBox = QComboBox()
        self.groupBox.setMinimumWidth(200)
        self.xChannelBox = QComboBox()  
        self.xChannelBox.setMinimumWidth(250)
        self.yChannelBox = QComboBox()  
        self.yChannelBox.setMinimumWidth(250)
        button1 = QPushButton(u"Select File")
        button1.setMaximumWidth(100)
        button2 = QPushButton(u"Plot")
        button2.setMaximumWidth(100)
        
        #connect SIGNALs
        self.connect(button1, SIGNAL('clicked()'), self.selectFile)
        self.connect(button2, SIGNAL('clicked()'), self.plot)
        
        #add to Layout
        layout.addWidget(self.fileTextWindow,0,0,1,3)
        layout.addWidget(button1,0,3)
        layout.addWidget(self.groupBox,1,0)
        layout.addWidget(self.xChannelBox,1,1)
        layout.addWidget(self.yChannelBox,1,2)
        layout.addWidget(button2,1,3)
        layout.columnStretch(4)
        
        #initialize store for TDMSfiles
        self.tdmsFile = None
        self.groupList = []
        self.ChannelList = []
        self.widget = None
        
    def selectFile(self):
        self.fileTextWindow.setText(QFileDialog.getOpenFileName(self,u"Open File","",u"TDMS (*.tdms)"))
        #read TdmsFile an fill groupBox        
        self.tdmsFile = nptdms.TdmsFile(self.fileTextWindow.toPlainText())
        self.groupList = self.tdmsFile.groups()
        self.groupBox.clear()
        for group in self.groupList:
            self.groupBox.addItem(group)
        #connect signal to activated
        self.groupBox.activated['QString'].connect(self.fillChannelBoxes)

    def fillChannelBoxes(self,index):
        self.channelList = self.tdmsFile.group_channels(self.groupList[self.groupBox.currentIndex()])
        #empty channelBox        
        self.xChannelBox.clear()
        self.yChannelBox.clear()
        #fill with new channels                
        for channel in self.channelList:
            self.xChannelBox.addItem(re.search(r"'/'(.+)'",channel.path).group(1))
            self.yChannelBox.addItem(re.search(r"'/'(.+)'",channel.path).group(1))
        
    def plot(self):
        x = self.channelList[self.xChannelBox.currentIndex()].data
        y = self.channelList[self.yChannelBox.currentIndex()].data
        self.widget = plotWidget(self,x,y,lambda x: x/2)
        self.widget.setup_widget("bla")        
        self.layout().addWidget(self.widget,2,0,1,4)
        
def previewTransportData():
    """
    Preview transport measurement data
    """
    # -- Create QApplication
    import guidata
    _app = guidata.qapplication()
    # --
    win = previewTransportDataWindow()
    
    win.show()
    _app.exec_()
    
    from lib.transportdata  import antiSymmetrizeSignalUpDown
    # onchange text_box_tmds_file: load Tdms File
    
    # onload tmds_file: Read Groups and populate group select box
    
    # onchange group_select_box: read channels of group and populate second select box
    
    # onchange channel_select_box;
    #  read data and plot
    
    # onchange symmetrize(difference, sum, raw); onchange normalize(to 
    # max/min/mean/custom value); onchange average up_down_sweep:
    #   process raw data according to selected options and replace existing plot curve
    #   display signal statistics
    # Bonus points: keep raw data associated with a curve in memory so an arbitrary
    # number of curves can be plotted and individually processed
    
    # Long term: Fit sin/cos
    
    curve = make.curve(x, y, "ab", "b")
    range = make.range(-2, 2)
    #disp0 = make.range_info_label(range, 'BR', u"x = %.1f ± %.1f cm",
    #                              title="Range infos")

    disp1 = make.computation(range, "BL", "trapz=%g",
                             curve, lambda x,y: np.trapz(y,x))

    disp2 = make.computations(range, "TL",
                              [(curve, "min=%.5f", lambda x,y: y.min()),
                               (curve, "max=%.5f", lambda x,y: y.max()),
                               (curve, "avg=%.5f", lambda x,y: y.mean())])
    legend = make.legend("TR")
    plot( curve, range, disp1, disp2, legend)

if __name__ == "__main__":
    previewTransportData()
