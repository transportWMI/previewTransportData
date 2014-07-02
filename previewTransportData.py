# -*- coding: utf-8 -*-
"""
Created on Mon Jun 23 10:27:50 2014

@author: hannes.maierflaig
"""
from guidata.qt.QtGui import QLabel, QIntValidator, QLineEdit, QCheckBox, QVBoxLayout, QMainWindow, QWidget, QComboBox, QGridLayout, QHBoxLayout, QFileDialog, QPushButton, QTextEdit
from guidata.qt.QtCore import SIGNAL

from guiqwt.plot import CurveDialog
from guiqwt.builder import make

import numpy as np
import nptdms
import re
import logging as l 
import lib.transportdata as transdat

l.basicConfig(format='%(levelname)s:%(message)s', level=l.DEBUG)

def qwtArrayDoubleToList(array):
    x = []
    for i in range(0,array.size()):
        x.append(array[i])
    return x    

def ndarrayToList(array):
    x = []
    for i in range(0,np.size(array)):
        x.append(array[i])
    return x
    
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
        

        # Initialize layout    
        # Preprocessing
        self.comboBoxDeltaMethod = QComboBox()
        self.comboBoxDeltaMethod.addItem(u"Raw data [n]")        
        self.comboBoxDeltaMethod.addItem(u"Raw data [2n-1]")
        self.comboBoxDeltaMethod.addItem(u"Raw data [2n]")
        self.comboBoxDeltaMethod.addItem(u"Diff ([2n-1]-[2n])/2")        
        self.comboBoxDeltaMethod.addItem(u"Sum ([2n-1]+[2n])/2")  
        self.checkBoxSymmetrize = QCheckBox("Symmetrize")
        self.checkBoxAntiSymmetrize = QCheckBox("Antisymmetrize")
        self.checkBoxAverage = QCheckBox("Average Up-Down-Sweep")
        self.checkBoxNorm = QCheckBox("Normalize")
        
        self.buttonCommit = QPushButton(u"Commit Changes")
        
        symmOffsetLabel = QLabel("Symmetry Step")
        self.symmOffsetField = QLineEdit() 
        self.symmOffsetField.setMaximumWidth(150)
        self.symmOffsetField.setValidator(QIntValidator())
        
        # Fitting
        self.buttonFit = QPushButton(u"fitButton")
        self.comboBoxFit = QComboBox()
        self.comboBoxFit.setMinimumWidth(200)
        self.comboBoxFit.addItem(u"cos()")
        self.comboBoxFit.addItem(u"cos²()")
        self.connect(self.buttonFit, SIGNAL('clicked()'), self.dispatchFit)

        
        # Connect SIGNALs
        self.connect(self.buttonCommit, SIGNAL('clicked()'), self.commitChanges)
        # should be removed if the button is used sooner or later
        self.checkBoxAntiSymmetrize.stateChanged.connect(self.updateCheckboxes)        
        self.checkBoxSymmetrize.stateChanged.connect(self.updateCheckboxes)        
        self.checkBoxNorm.stateChanged.connect(self.updateCheckboxes)        
        self.checkBoxAverage.stateChanged.connect(self.updateCheckboxes)        
                
        # Make layout        
        #  first row
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.comboBoxDeltaMethod)
        hlayout.addWidget(self.checkBoxNorm)
        hlayout.addWidget(self.checkBoxAverage)
        hlayout.addWidget(self.checkBoxSymmetrize)
        hlayout.addWidget(self.checkBoxAntiSymmetrize)
        hlayout.addWidget(self.buttonCommit)
        #  second row
        hlayout2 = QHBoxLayout()
        hlayout2.addStretch(2)
        hlayout2.addWidget(symmOffsetLabel)
        hlayout2.addWidget(self.symmOffsetField)
        hlayout2.addWidget(self.comboBoxFit)
        hlayout2.addWidget(self.buttonFit)
        #  vertical layout
        vlayout = QVBoxLayout()
        vlayout.addLayout(hlayout)
        vlayout.addLayout(hlayout2)
        vlayout.addWidget(self.curveDialog)
        self.setLayout(vlayout)
        
    # Here happens the stuff you want to apply to the data @ commit and before plotting
    def processData(self):
        if self.comboBoxDeltaMethod.currentIndex() == 0:
            # plain raw data
            x = self.x
            y = self.y
        elif self.comboBoxDeltaMethod.currentIndex() == 1:
            # odd raw data values
            x = transdat.separateAlternatingSignal(self.x)[0]
            y = transdat.separateAlternatingSignal(self.y)[0]
        elif self.comboBoxDeltaMethod.currentIndex() == 2:
            # even raw data values
            x = transdat.separateAlternatingSignal(self.x)[1]
            y = transdat.separateAlternatingSignal(self.y)[1]
        elif self.comboBoxDeltaMethod.currentIndex() == 3:
            # difference of odd - even values
            x = transdat.separateAlternatingSignal(self.x)[0]
            y = transdat.separateAlternatingSignal(self.y)[0] -  transdat.separateAlternatingSignal(self.y)[1]
        elif self.comboBoxDeltaMethod.currentIndex() == 4:
            # difference of odd - even values
            x = transdat.separateAlternatingSignal(self.x)[0]
            y = transdat.separateAlternatingSignal(self.y)[0] +  transdat.separateAlternatingSignal(self.y)[1]
            
        if self.average:
            x = transdat.averageUpDownSweep(x)
            y = transdat.averageUpDownSweep(y)
        if self.norm:
            y = y-min(y)
        if self.symmetrize:
            y = transdat.symmetrizeSignal(y)
        if self.antiSymmetrize:
            y = transdat.antiSymmetrizeSignal(y)
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
        """
        FIXME: What do you need this for? 
        FIXME: Document what i's supposed to do (nothing obviously)
        """
        self.average = self.checkBoxAverage.checkState()
        self.symmetrize = self.checkBoxSymmetrize.checkState()
        self.antiSymmetrize = self.checkBoxAntiSymmetrize.checkState()
        self.norm = self.checkBoxNorm.checkState()

    # %% Fitting routines    
    def dispatchFit(self):
        """
        Choose correct fit routine according to comboBoxFit.currentIndex() and 
        execute the appropriate function.
        """
        # list of available fit routines
        if self.comboBoxFit.currentIndex() == 0:
            self.fitCos(self.plot.get_selected_items()[0])
        elif self.comboBoxFit.currentIndex() == 1:
            self.fitCosSq(self.plot.get_selected_items()[0])
                        
    def fitCos(self, curveItem):
        """ 
        Fit a cosin to the curve stored in curveItem and plot
        
        FIXME: qwtdata comes with quite nice fitting tools. use them instead of tayloring your own stuff again...
        Parameters
        -----------
        curveItem : guiqwt.curve.CurveItem 
            retrieve e.g. w/ win.widget.plot.get_selected_items()[0]
        """
        # get data from curve (this is actually "built-in method x of QwtArrayData object")
        # and does not have iterators implemented
        x = np.array(qwtArrayDoubleToList(curveItem.data().xData()))
        y = np.array(qwtArrayDoubleToList(curveItem.data().yData()))

        # fit using a cosin
        amplitude, frequency, phase, y0 , yFit= transdat.fitcos(ndarrayToList(x),ndarrayToList(y), fitY0 = True)
    
        self.plot.add_item(make.curve(ndarrayToList(x),ndarrayToList(yFit),color='r'))
        self.plot.replot()
        print(amplitude, frequency, phase, y0)
        

    def fitCosSq(self, curveItem):
        """ Untested. Probably not working yet """
        x = np.array(qwtArrayDoubleToList(curveItem.data().xData()))
        y = np.array(qwtArrayDoubleToList(curveItem.data().yData()))

        # fit using a cosin
        amplitude, frequency, phase, y0 , yFit= transdat.fitcos_squared(ndarrayToList(x),ndarrayToList(y), fitY0 = True)
    
        self.plot.add_item(make.curve(ndarrayToList(x),ndarrayToList(yFit),color='r'))
        self.plot.replot()
        print(amplitude, frequency, phase, y0)



        
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
        
        # Connect SIGNALs
        self.connect(button1, SIGNAL('clicked()'), self.selectFile)
        self.connect(self.plotButton, SIGNAL('clicked()'), self.plot)
        
        # Build Layout
        layout.addWidget(self.fileTextWindow,0,0,1,3)
        layout.addWidget(button1,0,3)
        layout.addWidget(self.groupBox,1,0)
        layout.addWidget(self.xChannelBox,1,1)
        layout.addWidget(self.yChannelBox,1,2)
        layout.addWidget(self.plotButton,1,3)
        layout.columnStretch(4)
        
        # Initialize store for TDMSfiles
        self.tdmsFile = None
        self.groupList = []
        self.ChannelList = []
    
        # Initialize memory for last selected x and y channel
        self.selectedXChannel = 0
        self.selectedYChannel = 0
                
        # Initialize plot widget
        self.widget = plotWidget(self)
        self.layout().addWidget(self.widget,2,0,1,4)
        self.widget.buttonCommit.setEnabled(False)
        self.plotButton.setEnabled(False)
        
    def selectFile(self):
        self.fileTextWindow.setText(QFileDialog.getOpenFileName(self,u"Open File","",u"TDMS (*.tdms);;All files (*.*)"))
        #read TdmsFile an fill groupBox        
        self.tdmsFile = nptdms.TdmsFile(self.fileTextWindow.toPlainText())
        self.groupBox.clear()
        self.groupList = []
        for group in self.tdmsFile.groups():
            if group.startswith("Read."):
                self.groupBox.addItem(group)
                self.groupList.append(group)

        # Connect signal to activated
        self.groupBox.activated['QString'].connect(self.fillChannelBoxes)

    def fillChannelBoxes(self,index):
        self.channelList = self.tdmsFile.group_channels(self.groupList[self.groupBox.currentIndex()])
        
        # Empty channelBox        
        self.xChannelBox.clear()
        self.yChannelBox.clear()
        
        # Fill with new channels                
        for channel in self.channelList:
            self.xChannelBox.addItem(re.search(r"'/'(.+)'",channel.path).group(1))
            self.yChannelBox.addItem(re.search(r"'/'(.+)'",channel.path).group(1))

        # Select the last selected index automatically is possible
        if self.selectedXChannel > 0 and self.selectedXChannel < self.xChannelBox.count():
            self.xChannelBox.setCurrentIndex(self.selectedXChannel)
        if self.selectedYChannel > 0 and self.selectedYChannel < self.yChannelBox.count():
            self.yChannelBox.setCurrentIndex(self.selectedYChannel)

        self.plotButton.setEnabled(True)
        
    def plot(self):
        self.widget.buttonCommit.setEnabled(True)
        x = self.channelList[self.xChannelBox.currentIndex()].data
        y = self.channelList[self.yChannelBox.currentIndex()].data
        
        self.selectedXChannel = self.xChannelBox.currentIndex()
        self.selectedYChannel = self.yChannelBox.currentIndex()
        
        self.widget.newData(x,y)
        
#def previewTransportData():
#    """
#    Preview transport measurement data
#    """
#    # -- Create QApplication
import guidata
_app = guidata.qapplication()
# --
win = previewTransportDataWindow()

win.show()
#    _app.exec_()
    
     
    # onchange symmetrize(difference, sum, raw); onchange normalize(to 
    # max/min/mean/custom value); onchange average up_down_sweep:
    #   process raw data according to selected options and replace existing plot curve
    #   display signal statistics
    # Bonus points: keep raw data associated with a curve in memory so an arbitrary
    # number of curves can be plotted and individually processed
    
    # Long term: Fit sin/cos
    


if __name__ == "__main__":
    previewTransportData()
