# -*- coding: utf-8 -*-
"""
Created on Mon Jun 23 10:27:50 2014

@author: hannes.maierflaig
"""
from guidata.qt.QtGui import QLabel, QDoubleValidator, QIntValidator, QLineEdit, QCheckBox, QVBoxLayout, QMainWindow, QWidget, QComboBox, QGridLayout, QHBoxLayout, QFileDialog, QPushButton, QGroupBox
from guidata.qt.QtCore import SIGNAL

from guiqwt.plot import CurveDialog
from guiqwt.builder import make

import numpy as np
import nptdms
import re
from DataObject import DataObject
import transportdata as transdat

import logging
logging.basicConfig()
l = logging.getLogger(__name__)
l.setLevel(logging.DEBUG)

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
        
        self.labelSymmStep = QLabel(u"")
        self.labelSymmStep.setEnabled(False)
        self.lineEditSymmStep = QLineEdit() 
        self.lineEditSymmStep.setMaximumWidth(150)
        self.lineEditSymmStep.setValidator(QIntValidator())
        self.lineEditSymmStep.setEnabled(False)
        
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
        self.connect(self.buttonAutoscale, SIGNAL('clicked()'), self.autoScale)              
        self.connect(self.checkBoxAdmrData, SIGNAL('stateChanged(int)'), self.uiSymmetrization)
        self.connect(self.comboBoxSymmetrize, SIGNAL('currentIndexChanged(QString)'), self.uiSymmetrization)

        # Make layout        

        # Data processing
        vLayoutData  = QVBoxLayout()
                
        self.hLayoutData0 = QHBoxLayout() # to be filled dynamically 
        
        hLayoutData1 = QHBoxLayout()
        hLayoutData1.addWidget(self.comboBoxDeltaMethod)
        hLayoutData1.addWidget(self.checkBoxAverage)
        hLayoutData1.addWidget(self.comboBoxOffset)
        hLayoutData1.addWidget(self.lineEditOffset)
        hLayoutData1.addWidget(self.comboBoxNorm)
        
        hLayoutData2 = QHBoxLayout()
        hLayoutData2.addWidget(self.comboBoxSymmetrize)
        hLayoutData2.addWidget(self.checkBoxAdmrData)
        hLayoutData2.addWidget(self.labelSymmStep)
        hLayoutData2.addWidget(self.lineEditSymmStep)
#        hLayoutData2.addWidget(self.buttonPlot)

        vLayoutData.addLayout(self.hLayoutData0)
        vLayoutData.addLayout(hLayoutData1)
        vLayoutData.addLayout(hLayoutData2)
        
        groupDataProcess = QGroupBox("Processing")
        groupDataProcess.setLayout(vLayoutData)

        # Data fitting
        hlayout3 = QHBoxLayout()
        hlayout3.addStretch(1)
        hlayout3.addWidget(self.comboBoxFit)
        hlayout3.addWidget(self.buttonFit)
        hlayout3.addWidget(self.buttonResidual)
        hlayout3.addWidget(self.buttonAutoscale)
        
        groupDataFit = QGroupBox("Fitting and Plotting")
        groupDataFit.setLayout(hlayout3)
        
        #  Putting it all together
        vlayout = QVBoxLayout()
        vlayout.addWidget(groupDataProcess)
        vlayout.addWidget(groupDataFit)
        vlayout.addWidget(self.curveDialog)
        self.setLayout(vlayout)
            
            
    def uiSymmetrization(self, state):
        """ 
        Change UI (enabled state of text box etc) on selecting (anti-)symmetrization
        method
        """
        l.debug("Symmetrization method changed to %d"%self.comboBoxSymmetrize.currentIndex())
        if self.comboBoxSymmetrize.currentIndex() > 0:
            self.checkBoxAdmrData.setEnabled(True)
            self.labelSymmStep.setEnabled(True)
            self.lineEditSymmStep.setEnabled(True)
            if self.checkBoxAdmrData.checkState():
                self.labelSymmStep.setText("Symmetry step [in units of data points]")
            else:
                self.labelSymmStep.setText("Center of symmetrization [data point index]")
            
        else:
            self.checkBoxAdmrData.setEnabled(False)
            self.labelSymmStep.setEnabled(False)
            self.lineEditSymmStep.setEnabled(False)
        
        
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
        self.plot.add_item(make.curve(x,y,color='b',marker='Ellipse', markerfacecolor='b', title = currentDataObject.label))
        self.plot.do_autoscale()
        
    def newData(self,x,y, label = None):
        """
        Adds new data to the plot after recalculating everything as specified by the GUI
        
        Parameters
        --------
        x: np.array contains the data used for the x-axis
        y: np.array contains the data used for the y-axis        
        """
        self.listOfDataObjects.append(DataObject(x,y, label = label))
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
        if len(self.plot.get_selected_items()) == 0:
            l.warn("No curve selected to fit.")
            return False
            
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
        self.fileTextWindow = QLineEdit()
        self.groupBox = QComboBox()
        self.groupBox.setMinimumWidth(200)        
        self.groupBox.addItem("Data group")
        self.groupBox.setDisabled(1)
        self.fieldChannelBox = QComboBox()
        self.fieldChannelBox.setMinimumWidth(100)
        self.fieldChannelBox.addItem("Non-Unique Field Channel")
        self.fieldChannelBox.setDisabled(1)
        self.fieldBox = QComboBox()
        self.fieldBox.setMinimumWidth(50)
        self.fieldBox.setMaximumWidth(50)
        self.fieldBox.addItem("")
        self.fieldBox.setDisabled(1)
        self.xChannelBox = QComboBox()  
        self.xChannelBox.setMinimumWidth(250)
        self.xChannelBox.addItem("X-Channel")
        self.xChannelBox.setDisabled(1)        
        self.yChannelBox = QComboBox()  
        self.yChannelBox.setMinimumWidth(250)
        self.yChannelBox.addItem("Y-Channel")
        self.yChannelBox.setDisabled(1)        
        buttonFile = QPushButton(u"Select File")
        buttonFile.setMaximumWidth(100)
        self.buttonPlot = QPushButton(u"Plot")
        self.buttonPlot.setMaximumWidth(100)
        
        # Connect SIGNALs
        self.connect(buttonFile, SIGNAL('clicked()'), self.selectFile)
        self.connect(self.buttonPlot, SIGNAL('clicked()'), self.plot)
        
        # Build Layout
        layout.addWidget(self.fileTextWindow,0,0,1,5)
        layout.addWidget(buttonFile,0,5)
        layout.addWidget(self.groupBox,1,0)
        layout.addWidget(self.fieldChannelBox,1,1)
        layout.addWidget(self.fieldBox,1,2)
        layout.addWidget(self.xChannelBox,1,3)
        layout.addWidget(self.yChannelBox,1,4)
        layout.addWidget(self.buttonPlot,1,5)
        layout.columnStretch(5)
        
        # Initialize store for TDMSfiles
        self.tdmsFile = None
        self.groupList = []
        self.ChannelList = []
                
        # Initialize plot widget
        self.widget = plotWidget(self)
        self.layout().addWidget(self.widget,2,0,1,6)
        self.buttonPlot.setEnabled(False)
        
    def selectFile(self):
        """
        Reads the .tdms file written in self.fileTextWindow and populates self.groupBox with the groups of the .tdms file.
        """
        self.fileTextWindow.setText(QFileDialog.getOpenFileName(self,u"Open File","",u"TDMS (*.tdms);;All files (*.*)"))
        # Read TdmsFile and fill groupBox        
        self.tdmsFile = nptdms.TdmsFile(self.fileTextWindow.text())
        self.groupBox.clear()
        self.groupList = []
        for group in self.tdmsFile.groups():
            if group.startswith("Read."):
                self.groupBox.addItem(group)
                self.groupList.append(group)
        self.groupBox.setEnabled(1)
        # Fill channel boxes when group box is activated
        self.groupBox.activated['QString'].connect(self.fillChannelBoxes)       


    def fillChannelBoxes(self,index):
        """
        Populate self.xChannelBox and self.yChannelBox with the channels of the selected group
        If possible, uses the channels selected the previous time.
        """
        self.channelList = self.tdmsFile.group_channels(self.groupList[self.groupBox.currentIndex()])
        
        # Store currently selected channels
        selectedFieldChannel = self.fieldChannelBox.currentIndex()
        selectedXChannel = self.xChannelBox.currentIndex()
        selectedYChannel = self.yChannelBox.currentIndex()    

        # Empty channelBox      
        self.fieldChannelBox.clear()
        self.fieldChannelBox.addItem("No multiple fields in file")
        self.xChannelBox.clear()
        self.yChannelBox.clear()
        
        # Fill with new channels                
        for channel in self.channelList:
            self.fieldChannelBox.addItem(re.search(r"'/'(.+)'",channel.path).group(1))
            self.xChannelBox.addItem(re.search(r"'/'(.+)'",channel.path).group(1))
            self.yChannelBox.addItem(re.search(r"'/'(.+)'",channel.path).group(1))

        # Recall selected channels
        self.fieldChannelBox.setCurrentIndex(selectedFieldChannel)
        self.xChannelBox.setCurrentIndex(selectedXChannel)
        self.yChannelBox.setCurrentIndex(selectedYChannel)

        # Enable boxes
        self.fieldChannelBox.setEnabled(1)
        self.xChannelBox.setEnabled(1)
        self.yChannelBox.setEnabled(1)
        self.buttonPlot.setEnabled(1)
        
        # Recalculate available fields when changing the field channel         
        self.fieldChannelBox.activated['QString'].connect(self.fillFieldBox)
     
     
    def fillFieldBox(self,index):
        """
        Populate field combo box with unique fields from channel selected in
        self.fieldChannelBox
        """
        # Get unique fields and sort by index (thus by order of measurement)
        fields, uniqueFieldStartIdx = np.unique(self.channelList[self.fieldChannelBox.currentIndex()-1].data, return_index=True)
        fields = fields[np.argsort(uniqueFieldStartIdx)]
        l.debug("Found %d fields in channel %s: "%(np.size(fields), str(self.fieldChannelBox.currentText())))
        
        # Populate combo box
        self.fieldBox.clear()
        for field in fields:
            self.fieldBox.addItem("%.2fT"%field)
            
        self.fieldBox.setEnabled(1)
        
        
    def plot(self):
        """
        Hands new data to the plotWidget() to be displayed (or to be appended to the display)
        
        """
        rawX = self.channelList[self.xChannelBox.currentIndex()].data
        rawY = self.channelList[self.yChannelBox.currentIndex()].data
        
        if self.fieldChannelBox.currentIndex() > 0:
            rawField = self.channelList[self.fieldChannelBox.currentIndex()-1].data
        
            dataStruct = transdat.preprocessTransportData(rawField, rawX, rawY,delta_method = False)
            
            fieldLabel = "%.2fT"%dataStruct[self.fieldBox.currentIndex()]["field"]
            x = dataStruct[self.fieldBox.currentIndex()-1]["angle"]
            y = dataStruct[self.fieldBox.currentIndex()-1]["signal"]
        else:
            fieldLabel = None
            x = rawX
            y = rawY
            
        l.debug("Adding data with label \"%s\", len(x) = %d, len(y) = %d."%(str(fieldLabel), len(x), len(y)))
           
        self.widget.newData(x,y, label = fieldLabel)
        
        
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
