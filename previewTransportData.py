# -*- coding: utf-8 -*-
"""
Created on Mon Jun 23 10:27:50 2014

@author: hannes.maierflaig
"""
from guidata.qt.QtGui import QLabel, QIntValidator, QLineEdit, QCheckBox, QVBoxLayout, QMainWindow, QWidget, QComboBox, QGridLayout, QHBoxLayout, QFileDialog, QPushButton, QTextEdit
from guidata.qt.QtCore import SIGNAL

from guiqwt.plot import CurveDialog
from guiqwt.builder import make

from scipy import optimize
import numpy as np
import nptdms
import re

import lib.transportdata as transdat

class plotWidget(QWidget):
    """
    Will be done soon
    """
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.setMinimumSize(500, 500)

        #flag initialization
        self.average = False
        self.symmetrize = False
        self.antiSymmetrize = False
        self.fitCosSq = False
        self.fitCos = False
        self.norm = False

        #initialize data storage
        self.symmStep = None
        self.x = None
        self.y = None
        self.storageArray = []
        
        #initialize plot widget
        self.curveDialog = CurveDialog(edit=False,toolbar=True)
        self.curveDialog.get_itemlist_panel().show()
              
        self.plot = self.curveDialog.get_plot()
        self.plot.set_antialiasing(True)
        self.plot.do_autoscale()
        
        # initialize layout    
        self.checkBoxSymm = QCheckBox("Symmetrize")
        self.checkBoxAnti = QCheckBox("Antisymmetrize")
        self.checkBoxAverage = QCheckBox("Average")
        self.checkBoxFitCosSq = QCheckBox("Fit Cos^2")
        self.checkBoxFitCos = QCheckBox("Fit Cos")
        self.checkBoxNorm = QCheckBox("Normalize")
        
        self.commitButton = QPushButton(u"Commit Changes")
        
        symmOffsetLabel = QLabel("Symmetry Step")
        self.symmOffsetField = QLineEdit() 
        self.symmOffsetField.setMaximumWidth(150)
        self.symmOffsetField.setValidator(QIntValidator())
        
        
        # connect SIGNALs
        self.connect(self.commitButton, SIGNAL('clicked()'), self.commitChanges)
        # should be removed if the button is used sooner or later
        self.checkBoxAnti.stateChanged.connect(self.updateCheckboxes)        
        self.checkBoxSymm.stateChanged.connect(self.updateCheckboxes)        
        self.checkBoxNorm.stateChanged.connect(self.updateCheckboxes)        
        self.checkBoxFitCos.stateChanged.connect(self.updateCheckboxes)        
        self.checkBoxFitCosSq.stateChanged.connect(self.updateCheckboxes)        
        self.checkBoxAverage.stateChanged.connect(self.updateCheckboxes)        
                
        # make layout        
        #  first row
        hlayout = QHBoxLayout()
        hlayout.addStretch(1)
        hlayout.addWidget(self.checkBoxNorm)
        hlayout.addWidget(self.checkBoxAverage)
        hlayout.addWidget(self.checkBoxSymm)
        hlayout.addWidget(self.checkBoxAnti)
        hlayout.addWidget(self.checkBoxFitCos)
        hlayout.addWidget(self.checkBoxFitCosSq)
        hlayout.addWidget(self.commitButton)
        #  second row
        hlayout2 = QHBoxLayout()
        hlayout2.addStretch(5)
        hlayout2.addWidget(symmOffsetLabel)
        hlayout2.addWidget(self.symmOffsetField)
        #  vertical layout
        vlayout = QVBoxLayout()
        vlayout.addLayout(hlayout)
        vlayout.addLayout(hlayout2)
        vlayout.addWidget(self.curveDialog)
        self.setLayout(vlayout)
        
    # Here happens the stuff you want to apply to the data @ commit and befor plot
    def processData(self):
        x = self.x
        y = self.y
        if self.average:
            x = x
        if self.norm:
            y = y-max(y)
        if self.symmetrize:
            y = transdat.SymmetrizeSignal(y)
        if self.antiSymmetrize:
            y = transdat.antiSymmetrizeSignal(y)
        if self.fitCos:
            fitfunc = lambda p,x: p[0]*np.sin(np.pi*(x-p[2])/p[1])+p[3]
            errfunc = lambda p,x,y: fitfunc(p,x) - y
            p0 = [max(y)-min(y),360,0,min(y)]
            p1, success = optimize.leastsq(errfunc, p0[:],args=(x,y))
            angle = np.linspace(x.min(),x.max(),4*len(x))
            self.plot.add_item(make.curve(angle,fitfunc(p1,angle),color='r'))
        if self.fitCosSq:
            fitfunc = lambda p,x: p[0]*np.cos(np.pi*(x-p[1])/p[2])**2+p[3]
            errfunc = lambda p,x,y: fitfunc(p,x) - y
            p0 = [max(y)-min(y),0,180,(max(y)-min(y))/2]
            p1, success = optimize.leastsq(errfunc, p0[:],args=(x,y),factor = 0.1)
            print success
            print p1
            angle = np.linspace(x.min(),x.max(),4*len(x))
            self.plot.add_item(make.curve(angle,fitfunc(p1,angle),color='r'))
        return (x,y)
    
    def commitChanges(self):
        self.updateCheckboxes(0);
        (x,y) = self.processData()
        self.plot.add_item(make.curve(x,y,color='b',marker='Ellipse', markerfacecolor='b'))
        self.storageArray.append((x,y))
        self.plot.do_autoscale()  
        
    def newData(self,x,y):
        self.x = x
        self.y = y
        self.commitChanges()
    
    def updateCheckboxes(self,i):
        self.average = self.checkBoxAverage.checkState()
        self.symmetrize = self.checkBoxSymm.checkState()
        self.antiSymmetrize = self.checkBoxAnti.checkState()
        self.fitCosSq = self.checkBoxFitCosSq.checkState()
        self.fitCos = self.checkBoxFitCos.checkState()
        self.norm = self.checkBoxNorm.checkState()

        
class previewTransportDataWindow(QWidget):
    '''
    Will be done soon!
    '''
    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowTitle("previewTransportData")

        #Initialize Layout    
        layout = QGridLayout()
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
        self.plotButton = QPushButton(u"Plot")
        self.plotButton.setMaximumWidth(100)
        
        #connect SIGNALs
        self.connect(button1, SIGNAL('clicked()'), self.selectFile)
        self.connect(self.plotButton, SIGNAL('clicked()'), self.plot)
        
        #add to Layout
        layout.addWidget(self.fileTextWindow,0,0,1,3)
        layout.addWidget(button1,0,3)
        layout.addWidget(self.groupBox,1,0)
        layout.addWidget(self.xChannelBox,1,1)
        layout.addWidget(self.yChannelBox,1,2)
        layout.addWidget(self.plotButton,1,3)
        layout.columnStretch(4)
        
        #initialize store for TDMSfiles
        self.tdmsFile = None
        self.groupList = []
        self.ChannelList = []
        
        #initialize plot widget
        self.widget = plotWidget(self)
        self.layout().addWidget(self.widget,2,0,1,4)
        self.widget.commitButton.setEnabled(False)
        self.plotButton.setEnabled(False)
        
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
        self.plotButton.setEnabled(True)
        
    def plot(self):
        self.widget.commitButton.setEnabled(True)
        x = self.channelList[self.xChannelBox.currentIndex()].data
        y = self.channelList[self.yChannelBox.currentIndex()].data
        self.widget.newData(x,y)
        
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
    
     
    # onchange symmetrize(difference, sum, raw); onchange normalize(to 
    # max/min/mean/custom value); onchange average up_down_sweep:
    #   process raw data according to selected options and replace existing plot curve
    #   display signal statistics
    # Bonus points: keep raw data associated with a curve in memory so an arbitrary
    # number of curves can be plotted and individually processed
    
    # Long term: Fit sin/cos
    


if __name__ == "__main__":
    previewTransportData()
