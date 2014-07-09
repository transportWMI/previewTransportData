# -*- coding: utf-8 -*-
"""
Created on Mon Jun 23 10:27:50 2014

@author: hannes.maierflaig
"""
from guidata.qt.QtGui import QLabel, QDoubleValidator, QIntValidator, QLineEdit, QCheckBox, QVBoxLayout, QMainWindow, QWidget, QComboBox, QGridLayout, QHBoxLayout, QFileDialog, QPushButton, QTextEdit
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
    """
    Transforms a QWT array to a list
    """
    x = []
    for i in range(0,array.size()):
        x.append(array[i])
    return x    

def ndarrayToList(array):
    """
    Transforms a numpy array to a list
    """
    x = []
    for i in range(0,np.size(array)):
        x.append(array[i])
    return x
    
class dataObject():
    """
    Creates a data object containing data for x and y channel
    optional flags can be passed to the initializer for recalculation
    
    Parameters
    -------
    x : np.array
        x-channel data
    y : np.array
        y-channel data  
    
    Class Members
    ----------
    self.x : np.array
        original x-channel data
    self.y : np.array
        original y-channel data
    self.xCalc : np.array
        recalculated x-channel data (raw data until first process data was run)
    self.yCalc : np.array
        recalculated y-channel data (raw data until first process data was run)
     
    """
    def __init__(self,x,y):
        self.x = x
        self.y = y
        self.xCalc = x
        self.yCalc = y
        
    def processData(self,switchDeltaMethod = 0, flagAverage = False,
                 switchNormalize = 0, switchOffset = 0, valueOffset = 0,
                 switchSymmetrize = 0, flagADMR = False, valueSymmetrize = 0):
        """
        Processes the data of the dataObject(y) according to the flags and switches given

        Parameters
        ----------      
        switchDeltaMethod : int(0-4)
            0   -> no delta method [n] (default)
            1   -> uneven indexed raw data [2n-1]
            2   -> even indexed raw data [2n]
            3   -> difference ([2n-1]-[2n])/2
            4   -> sum ([2n-1]+[2n])/2
        flagAverage : boolean
            False   -> no averaging (default)
            True   -> average up and down sweep
        switchNormalize : int(0-2)
            0   -> no normalization (default)
            1   -> normalize y to min(y)
            2   -> normalize y to max(y)
        switchOffset : int(0-4)
            0   -> no offset correction (default)
            1   -> subtracts min(y)
            2   -> subtracts max(y)
            3   -> subtracts mean(y)
            4   -> subtracts value defined in valueOffset
        valueOffset : double 
            custom value to subtract from the data (if switchOffset = 4) (default = 0)
        switchSymmetrize : int(0-2)
            0   -> no symmetrization (default)
            1   -> symmetrization
            2   -> antisymmetrization
        flagADMR : boolean
            False   -> R(H) data (default)
            True    -> ADMR data
        valueSymmetrize : int
            value of the symmetry step (ADMR) or center for symmetrization (R(H)) (default = 0)
        """
        x = self.x
        y = self.y
        if switchDeltaMethod == 0:
            # plain raw data
            pass
        elif switchDeltaMethod == 1:
            # odd raw data values
            x = transdat.separateAlternatingSignal(self.x)[0]
            y = transdat.separateAlternatingSignal(self.y)[0]
        elif switchDeltaMethod == 2:
            # even raw data values
            x = transdat.separateAlternatingSignal(self.x)[1]
            y = transdat.separateAlternatingSignal(self.y)[1]
        elif switchDeltaMethod == 3:
            # difference of odd - even values
            x = transdat.separateAlternatingSignal(self.x)[0]
            y = transdat.separateAlternatingSignal(self.y)[0] -  transdat.separateAlternatingSignal(self.y)[1]
        elif switchDeltaMethod == 4:
            # difference of odd - even values
            x = transdat.separateAlternatingSignal(self.x)[0]
            y = transdat.separateAlternatingSignal(self.y)[0] +  transdat.separateAlternatingSignal(self.y)[1]
            
        if flagAverage:
            # average up and down sweep
            x = transdat.averageUpDownSweep(x)
            y = transdat.averageUpDownSweep(y)
        if 0 == switchNormalize:
            pass
        elif 1 == switchNormalize:
            # normalize by min(y)
            y = y/np.min(y)
        elif 2 == switchNormalize:
            # normalize by max(y)
            y = y/np.max(y)
        if 0 == switchOffset:
            pass
        elif 1 == switchOffset:
            # subtract min(y)
            dummy = np.min(y)
            for i in range(len(y)):
                y[i] = y[i] - dummy
        elif 2 == switchOffset:
            # subtract max(y)
            dummy = np.max(y)
            for i in range(len(y)):
                y[i] = y[i] - dummy
        elif 3 == switchOffset:
            # subtract mean(y)
            dummy = np.mean(y)
            for i in range(len(y)):
                y[i] = y[i] - dummy
        elif 4 == switchOffset:
            # subtract valueOffset
            for i in range(len(y)):
                y[i] = y[i] - valueOffset
        if 0 == switchSymmetrize:
            pass
        elif 1 == switchSymmetrize:
            if flagADMR:
                # symmetrize admr data around symmetry step
                y = transdat.symmetrizeSignalUpDown(y,valueSymmetrize)
                x = x[0:len(y)]
            else:
                # symmetrize r(h) data around center
                y = transdat.symmetrizeSignal(y,valueSymmetrize)
                x = x[0:len(y)][::-1]
                #x = x[valueSymmetrize:len(y)+valueSymmetrize]
        elif 2 == switchSymmetrize:
            if flagADMR:
                #antisymmetrize admr data around symmetry step
                y = transdat.antiSymmetrizeSignalUpDown(y,valueSymmetrize)
                x = x[0:len(y)]
            else:                
                # symmetrize r(h) data around center
                y = transdat.antiSymmetrizeSignal(y,valueSymmetrize)
                x = x[0:len(y)][::-1]
                #x = x[valueSymmetrize:len(y)+valueSymmetrize]
        
        self.xCalc = x
        self.yCalc = y
    
class plotWidget(QWidget):
    """
    Creates a widget to display and process data.
    Offers several ways to look at the data to see if the
    measurement's results are probable.
    
    Parameters
    --------
    """
    def __init__(self, parent):
        """
        Initializes the widget with several widgets to set plotting preferences and the window to plot the data
        """
        QWidget.__init__(self, parent)
        self.setMinimumSize(500, 500)

        #initialize data storage
        self.symmStep = None
        self.x = None
        self.y = None
        self.listOfDataObjects = []
        
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
        
        self.comboBoxSymmetrize = QComboBox()
        self.comboBoxSymmetrize.addItem(u"No symmetrization")
        self.comboBoxSymmetrize.addItem(u"Symmetrization")
        self.comboBoxSymmetrize.addItem(u"Antisymmetrization")
        self.checkBoxAdmrData = QCheckBox(u"ADMR data")
        self.checkBoxAntiSymmetrize = QCheckBox(u"Antisymmetrize")
        
        self.checkBoxAverage = QCheckBox(u"Average Up-Down-Sweep")
        
        self.comboBoxNorm = QComboBox()
        self.comboBoxNorm.addItem(u"No normalization")
        self.comboBoxNorm.addItem(u"Normalize to min(data)")
        self.comboBoxNorm.addItem(u"Normalize to max(data)")
           
        self.comboBoxOffset = QComboBox()
        self.comboBoxOffset.addItem(u"No offset to subtract")
        self.comboBoxOffset.addItem(u"Subtract min(data)")
        self.comboBoxOffset.addItem(u"Subtract max(data)")
        self.comboBoxOffset.addItem(u"Subtract mean(data)")
        self.comboBoxOffset.addItem(u"Subtract custom value")
        self.lineEditOffset = QLineEdit()
        self.lineEditOffset.setMaximumWidth(100)
        self.lineEditOffset.setValidator(QDoubleValidator())
        
        self.buttonCommit = QPushButton(u"Commit Changes")
        
        symmOffsetLabel = QLabel(u"Symmetry Step(ADMR)/Center for symmetrization")
        self.lineEditSymmStep = QLineEdit() 
        self.lineEditSymmStep.setMaximumWidth(150)
        self.lineEditSymmStep.setValidator(QIntValidator())
        
        # Fitting
        self.buttonFit = QPushButton(u"Fit")
        self.comboBoxFit = QComboBox()
        self.comboBoxFit.setMinimumWidth(200)
        self.comboBoxFit.addItem(u"cos()")
        self.comboBoxFit.addItem(u"cos²()")
        
        self.buttonResidual = QPushButton(u"Calculate Residual")
        
        self.buttonAutoscale = QPushButton(u"Autoscale")
        
        # Connect SIGNALs
        self.connect(self.buttonFit, SIGNAL('clicked()'), self.dispatchFit)
        self.connect(self.buttonResidual, SIGNAL('clicked()'), self.calculateResidual)
        self.connect(self.buttonCommit, SIGNAL('clicked()'), self.commitChanges)
        self.connect(self.buttonAutoscale, SIGNAL('clicked()'), self.autoScale)              
                
        # Make layout        
        #  first row
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.comboBoxDeltaMethod)
        hlayout.addWidget(self.checkBoxAverage)
        hlayout.addWidget(self.comboBoxOffset)
        hlayout.addWidget(self.lineEditOffset)
        hlayout.addWidget(self.comboBoxNorm)
        #  second row
        hlayout2 = QHBoxLayout()
        hlayout2.addStretch(2)
        hlayout2.addWidget(self.comboBoxSymmetrize)
        hlayout2.addWidget(self.checkBoxAdmrData)
        hlayout2.addWidget(symmOffsetLabel)
        hlayout2.addWidget(self.lineEditSymmStep)
        hlayout2.addWidget(self.buttonCommit)
        # third row
        hlayout3 = QHBoxLayout()
        hlayout3.addStretch(1)
        hlayout3.addWidget(self.comboBoxFit)
        hlayout3.addWidget(self.buttonFit)
        hlayout3.addWidget(self.buttonResidual)
        hlayout3.addWidget(self.buttonAutoscale)
        #  vertical layout
        vlayout = QVBoxLayout()
        vlayout.addLayout(hlayout)
        vlayout.addLayout(hlayout2)
        vlayout.addLayout(hlayout3)
        vlayout.addWidget(self.curveDialog)
        self.setLayout(vlayout)
            
            
    def autoScale(self):
        """
        Make the plot axis fit the data -> autoscale
        """
        self.plot.do_autoscale()
    
    def commitChanges(self):
        """
        Processes the data of the current data object and appends them to the plot window
        """
        currentDataObject = self.listOfDataObjects.pop()
        currentDataObject.processData(self.comboBoxDeltaMethod.currentIndex(),
                                      self.checkBoxAverage.isChecked(),self.comboBoxNorm.currentIndex(),
                                      self.comboBoxOffset.currentIndex(),(self.lineEditOffset.text().toDouble())[0],
                                      self.comboBoxSymmetrize.currentIndex(),self.checkBoxAdmrData.isChecked(),
                                      (self.lineEditSymmStep.text().toInt())[0])
        x = currentDataObject.xCalc
        y = currentDataObject.yCalc
        self.listOfDataObjects.append(currentDataObject)        
        self.plot.add_item(make.curve(x,y,color='b',marker='Ellipse', markerfacecolor='b'))
        self.plot.do_autoscale()
        
    def newData(self,x,y):
        """
        Adds new data to the plot after recalculating everything as specified by the GUI
        
        Parameters
        --------
        x: np.array contains the data used for the x-axis
        y: np.array contains the data used for the y-axis        
        """
        self.listOfDataObjects.append(dataObject(x,y))
        self.commitChanges()

    def calculateResidual(self):        
        """
        Calculate the residual of two selected curves and plot
        """
        x =  np.array(qwtArrayDoubleToList(self.plot.get_selected_items()[0].data().xData()))
        y1 = np.array(qwtArrayDoubleToList(self.plot.get_selected_items()[0].data().yData()))
        y2 = np.array(qwtArrayDoubleToList(self.plot.get_selected_items()[1].data().yData()))
        
        self.plot.add_item(make.curve(ndarrayToList(x),ndarrayToList(y2-y1),color='r'))
        self.plot.replot()
       

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
    """ 
    Create a widget to open a .tdms file and select a group and a channel to plot
    Data is stored in the seperate plot window that is appended to the bottom 
    (plotWidget(self)).
    
    Parameters    
    -----------
    """
    def __init__(self):
        """
        Initializes the layout and appends a plotWidget()
        """
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
        """
        Reads the .tdms file written in self.fileTextWindow and populates self.groupBox with the groups of the .tdms file.
        """
        self.fileTextWindow.setText(QFileDialog.getOpenFileName(self,u"Open File","",u"TDMS (*.tdms);;All files (*.*)"))
        #read TdmsFile and fill groupBox        
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
        """
        Populates self.xChannelBox and self.yChannelBox with the channels of the selected group
        If possible, uses the channels selected the previous time.
        """
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
        """
        Hands new data to the plotWidget() to be displayed (or to be appended to the display)
        """
        self.widget.buttonCommit.setEnabled(True)
        x = self.channelList[self.xChannelBox.currentIndex()].data
        y = self.channelList[self.yChannelBox.currentIndex()].data
        
        self.selectedXChannel = self.xChannelBox.currentIndex()
        self.selectedYChannel = self.yChannelBox.currentIndex()
        
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


if __name__ == "__main__":
    previewTransportData()
