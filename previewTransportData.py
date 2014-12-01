# -*- coding: utf-8 -*-
"""
Created on Mon Jun 23 10:27:50 2014

@author: hannes.maierflaig
"""
from guidata.qt.QtGui import QLabel, QDoubleValidator, QTextEdit, QLineEdit, QCheckBox, QVBoxLayout, QMainWindow, QWidget, QComboBox, QGridLayout, QHBoxLayout, QFileDialog, QPushButton, QGroupBox
from guidata.qt.QtCore import SIGNAL

from guiqwt.plot import CurveDialog
from guiqwt.builder import make
from guiqwt.signals import SIG_ACTIVE_ITEM_CHANGED

import numpy as np
import nptdms
import re
from lib.DataObject import DataObject
import lib.transportdata as transdat

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
    
class curveDialogIgnoreEsc(CurveDialog):
    """
    Creates a CurveDialog that ignores the termination via the Esc-key
    
    Construct a CurveDialog object: plotting dialog box with integrated 
    plot manager
        * wintitle: window title
        * icon: window icon
        * edit: editable state
        * toolbar: show/hide toolbar
        * options: options sent to the :py:class:`guiqwt.curve.CurvePlot` object
          (dictionary)
        * parent: parent widget
        * panels (optional): additionnal panels (list, tuple)
    --------    
    """
    def __init__(self, wintitle="guiqwt plot", icon="guiqwt.svg", edit=False,
                 toolbar=False, options=None, parent=None, panels=None):
        CurveDialog.__init__(self, wintitle, icon, edit,
                 toolbar, options, parent, panels)
    
    def closeEvent(self, event):
        event.ignore()
        l.error("Close event called - termination intercepted")
        
    def done(self,int):
        l.error("Esc key pressed - termination intercepted")
    
class widgetLogger(logging.Handler):
    """
    Creates a Handler that writes the logger's output to a QTextEdit.
    Output is formatted as debuglevel::name::message @ time
    
    Parameters
    ---------
    statusWidget: QTextEdit Widget where the output of the logger is written to
    debugLevel: Int DebugLevel of the handler to operate
    """
    def __init__(self, statusWidget, debugLevel):
        logging.Handler.__init__(self)
        self.setLevel(debugLevel)
        self.statusWidget = statusWidget
        self.formatter = logging.Formatter(fmt='%(levelname)s::%(name)s::%(message)s @ %(asctime)s')
        
    def emit(self,record):
        self.statusWidget.append(self.format(record))


#class FitInfo(ObjectInfo):
#    def __init__(self, params):
#        self.params = params
#
#    def get_text(self):
#        
#        return txt
        
    
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

        # Initialize data storage
        self.symmStep = None
        self.x = None
        self.y = None
        self.dataObjects = []   # holds the data and processing flags for each
                                # curve in the session needs to be held in sync
                                # with the plot list
        self.currentDataObject  = None # currently selected or plotted data object
                
        self.dataObjectTdmsFile  = [] # relates tdmsFiles to dataObjects 
        self.curveItemDataObject = []  # relates curveItems to dataObjects
        
        ## Initialize plot widget
        self.curveDialog = curveDialogIgnoreEsc(edit=False,toolbar=True)
        
        self.curveDialog.get_itemlist_panel().show()
              
        self.plot = self.curveDialog.get_plot()
        self.plot.set_antialiasing(True)
        
        
        ## Create Widgets
        # Processing
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
        self.checkBoxAdmrData.setDisabled(1)
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
        self.lineEditSymmStep.setValidator(QDoubleValidator())
        self.lineEditSymmStep.setEnabled(False)
        
        # Connect SIGNALs           
        self.connect(self.comboBoxOffset, SIGNAL('stateChanged(int)'), self.uiOffset)
        self.connect(self.checkBoxAdmrData, SIGNAL('stateChanged(int)'), self.uiSymmetrization)
        self.connect(self.comboBoxSymmetrize, SIGNAL('currentIndexChanged(QString)'), self.uiSymmetrization)
        self.connect(self.plot, SIG_ACTIVE_ITEM_CHANGED, self.updateGUI)
        # Processing
        vLayoutData  = QVBoxLayout()
    
        self.hLayoutData0 = QHBoxLayout() # to be filled dynamically 
        
        hLayoutData1 = QHBoxLayout()
        hLayoutData1.addWidget(self.comboBoxDeltaMethod)
        hLayoutData1.addWidget(self.checkBoxAverage)
        hLayoutData1.addWidget(self.comboBoxNorm)
        hLayoutData1.addWidget(self.comboBoxOffset)
        hLayoutData1.addWidget(self.lineEditOffset)
        
        hLayoutData2 = QHBoxLayout()
        hLayoutData2.addWidget(self.comboBoxSymmetrize)
        hLayoutData2.addWidget(self.checkBoxAdmrData)
        hLayoutData2.addWidget(self.labelSymmStep)
        hLayoutData2.addWidget(self.lineEditSymmStep)
        
        vLayoutData.addLayout(self.hLayoutData0)
        vLayoutData.addLayout(hLayoutData1)
        vLayoutData.addLayout(hLayoutData2)
        

        groupDataProcess = QGroupBox("Processing")
        groupDataProcess.setLayout(vLayoutData)
        
        #  Additional tools in toolbar
        toolbar = self.curveDialog.get_toolbar()
        toolbar.addAction("cos", self.fitCos)        
        toolbar.addAction(u"cos²", self.fitCosSq) 
        toolbar.addAction("residual", self.calculateResidual)
        toolbar.addSeparator()
        toolbar.addAction("autoscale", self.plot.do_autoscale)      
        toolbar.addSeparator()
        toolbar.addAction("ascii", self.export_ascii).setDisabled(0)      
        toolbar.addAction("code", self.export_objects).setDisabled(1)
        #  Putting it all together
        vlayout = QVBoxLayout()
        vlayout.addWidget(groupDataProcess)
        vlayout.addWidget(self.curveDialog)
        self.setLayout(vlayout)
        
    def updateGUI(self):
        """
        Update the GUI if another curve is activated
        """
        dataObject = self.findAssociatedDataObject()
        if(-1 == dataObject):
            l.error("GUI could not be updated")
            return
        
        dummyIndex = self.parent().comboBoxFile.findText(dataObject.path)
        self.parent().setCurrentTdmsFile(dummyIndex)
        
        dummyIndex = self.parent().groupBox.findText(dataObject.group)
        self.parent().groupBox.setCurrentIndex(dummyIndex)
        self.parent().groupBox.activated.emit(0) #int of SIGNAL is unused, take care if changed!       

        dummyIndex = self.parent().xChannelBox.findText(dataObject.xChannel)
        self.parent().xChannelBox.setCurrentIndex(dummyIndex)

        dummyIndex = self.parent().yChannelBox.findText(dataObject.yChannel)
        self.parent().yChannelBox.setCurrentIndex(dummyIndex)

        dummyIndex = self.parent().fieldChannelBox.findText(dataObject.paramChannel)
        self.parent().fieldChannelBox.setCurrentIndex(dummyIndex)
        self.parent().fieldChannelBox.activated.emit(dummyIndex) # is called once per previous call (e.g. 1 call after the first reload, 2 calls after second reload etc.)

        dummyIndex = self.parent().fieldBox.findText(dataObject.param)
        self.parent().fieldBox.setCurrentIndex(dummyIndex)
        
        l.debug(dataObject.operationsToString())
        self.readOperationsFromDataObject(dataObject)
        
                               
    def findAssociatedDataObject(self):
        """
        Find data object associated to currently selected curve
        """
        try:
            dataObject  = [v[1] for i, v in enumerate(self.curveItemDataObject) if v[0] == self.plot.get_selected_items()[0]][0]
        except:
            l.error("Could not find a data object associated to the currently selected curve. Maybe there's no curve selected?")
            return -1
        return dataObject
        
    def readOperationsFromDataObject(self,dataObject):
        """
        Get the parameters from the operations part of the dataObject to reset the GUI to
        the used parameters
        """
        self.resetFilters()
        for idx,operation in enumerate(dataObject.operations):
            if re.search(r"_deltaMethod",str(operation.__name__)):
                self.comboBoxDeltaMethod.setCurrentIndex(dataObject.operationParameters[idx]["method"])
            elif re.search(r"_averageUpDown",str(operation.__name__)):
                self.checkBoxAverage.setChecked(1)
            elif re.search(r"_offsetCorrection",str(operation.__name__)):
                self.comboBoxOffset.setCurrentIndex(dataObject.operationParameters[idx]["method"])
                self.lineEditOffset.setText(str(dataObject.operationParameters[idx]["offset"]))
            elif re.search(r"_symmetrize",str(operation.__name__)):
                self.comboBoxSymmetrize.setCurrentIndex(dataObject.operationParameters[idx]["method"])
                if dataObject.operationParameters[idx]["symm_step"]:
                    self.lineEditSymmStep.setText(str(dataObject.operationParameters[idx]["symm_step"]))
                    self.checkBoxAdmrData.setChecked(1)
                elif dataObject.operationParameters[idx]["symm_center"]:
                    self.lineEditSymmStep.setText(str(dataObject.operationParameters[idx]["symm_center"]))
            elif re.search(r"_normalize",str(operation.__name__)):
                self.comboBoxNormalize.setCurrentIndex(dataObject.operationParameters[idx]["method"])
           # elif re.search(r"_averageUpDown",str(operation.__name__)):               
                
    def resetFilters(self):
        """
        Resets the GUI for the filters back to the default state (all disabled)
        """
        self.checkBoxAdmrData.setChecked(0)
        self.checkBoxAntiSymmetrize.setChecked(0)
        self.checkBoxAverage.setChecked(0)
        self.comboBoxDeltaMethod.setCurrentIndex(0)
        self.comboBoxNorm.setCurrentIndex(0)
        self.comboBoxOffset.setCurrentIndex(0)
        self.comboBoxSymmetrize.setCurrentIndex(0)
        self.lineEditOffset.clear()
        self.lineEditSymmStep.clear()
        
    def export_ascii(self):
        """
        Save the (one) currently selected curve as ascii
        """
        dataObject = self.findAssociatedDataObject()
        
        if(-1 == dataObject):
            return
        
        fd = QFileDialog()
        fd.setDefaultSuffix(".dat")
        fd.setAcceptMode(QFileDialog.AcceptSave)
        fname = fd.getSaveFileName(self,u"Choose file to save","%s-%s-%s.dat"%(dataObject.path,dataObject.group,dataObject.yChannel),u"ASCII data file (*.dat);;All files (*.*)")
        
        dataObject.saveASCII(unicode(fname))


        
    def export_objects(self):
        return
            
    def uiSymmetrization(self, state):
        """ 
        Change UI (enabled state of text box etc) on selecting (anti-)symmetrization
        method
        """
        l.debug("Symmetrization method changed to %d"%self.comboBoxSymmetrize.currentIndex())
        if self.comboBoxSymmetrize.currentIndex() > 0: # any symm. method has been selected
            self.checkBoxAdmrData.setEnabled(True)
            self.labelSymmStep.setEnabled(True)
            self.lineEditSymmStep.setEnabled(True)
            if self.checkBoxAdmrData.checkState():
                self.labelSymmStep.setText("Symmetry step [in units x]")
            else:
                self.labelSymmStep.setText("Center of symmetrization [in units of x]")
        else:
            self.checkBoxAdmrData.setEnabled(False)
            self.labelSymmStep.setEnabled(False)
            self.lineEditSymmStep.setEnabled(False)


    def uiOffset(self, state):
        """ 
        Change enabled state of text box on selecting offset subtraction
        """
        l.debug("Symmetrization method changed to %d"%self.comboBoxSymmetrize.currentIndex())
        if (self.comboBoxOffset.currentIndex() == 0      # no offset subtraction
            or self.comboBoxOffset.currentIndex() == 4): # user defined value 
            self.lineEditOffset.setEnabled(True)
        else:
            self.lineEditOffset.setEnabled(False)
            
    
    def processAndPlotData(self):
        """
        Processes the data of the current data object and appends them to the plot window
        """
        currentDataObject = self.dataObjects.pop()
        
        # Queue operations
        currentDataObject.deltaMethod(self.comboBoxDeltaMethod.currentIndex())
        if self.checkBoxAverage.isChecked():
            currentDataObject.averageUpDown()
        if self.checkBoxAdmrData.isChecked():
            currentDataObject.symmetrize(self.comboBoxSymmetrize.currentIndex(),symm_step = (self.lineEditSymmStep.text().toDouble())[0])
        else:
            currentDataObject.symmetrize(self.comboBoxSymmetrize.currentIndex(),symm_center = (self.lineEditSymmStep.text().toDouble())[0])
        currentDataObject.normalize(self.comboBoxNorm.currentIndex())
        currentDataObject.offsetCorrection(self.comboBoxOffset.currentIndex(), offset = (self.lineEditOffset.text().toDouble())[0])

        x,y = currentDataObject.processData()
        l.debug(str(currentDataObject))
        
        self.dataObjects.append(currentDataObject)        
        curve = make.curve(x,y,color='b',marker='Ellipse', markerfacecolor='b', title = currentDataObject.label)
        self.plot.add_item(curve)
        self.plot.do_autoscale()
        curve.select()
        
        self.curveItemDataObject.append((curve, currentDataObject))
        
        
    def newData(self,x,y, label = None):
        """
        Adds new data to the plot after recalculating everything as specified by the GUI
        
        Parameters
        --------
        x: np.array contains the data used for the x-axis
        y: np.array contains the data used for the y-axis        
        """
        dataObject = DataObject(x,y, 
                               label = label,
                               path=self.parent().comboBoxFile.currentText(),
                               group = self.parent().groupBox.currentText(),
                               paramChannel = self.parent().fieldChannelBox.currentText(),
                               param = self.parent().fieldBox.currentText(),
                               xChannel = self.parent().xChannelBox.currentText(),
                               yChannel = self.parent().yChannelBox.currentText())
        self.dataObjects.append(dataObject)
        self.dataObjectTdmsFile.append((dataObject, self.parent().currentTdmsFile))

        self.processAndPlotData()


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
    def fitCos(self):
        """ 
        Fit a cosin^2 to the currently selected curve and plot the resulting fit function
        """
        if len(self.plot.get_selected_items()) == 0:
            l.warn("No curve selected to fit.")
            return False
        
        curveItem = self.plot.get_selected_items()[0]
        # get data from curve (this is actually "built-in method x of QwtArrayData object")
        # and does not have iterators implemented
        x = np.array(qwtArrayDoubleToList(curveItem.data().xData()))
        y = np.array(qwtArrayDoubleToList(curveItem.data().yData()))

        # fit using a cosin
        amplitude, frequency, phase, y0 , yFit= transdat.fitcos(ndarrayToList(np.deg2rad(x)),ndarrayToList(y), fitY0 = True)
    
        fitCurve = make.curve(ndarrayToList(x),ndarrayToList(yFit),
                              color='r',
                              title=u"cosfit(%s)"%curveItem.title().text())
        fitCurve.select()
        self.plot.add_item(fitCurve)

        l.info(u"cos fit: amplitude %.3e, frequency %.3e, phase %.3e, offset y0 %.3e"%(amplitude, frequency, phase, y0))
        label = make.label(u"""<i>cos()-fit (%s)</i><br/>
            amplitude %.3e<br/>
            period %.3e°<br/>
            phase %.3e°<br/>
            offset y0 %.3e
            """%(curveItem.title().text(), amplitude, np.rad2deg(2*np.pi/frequency), np.rad2deg(phase), y0),
            (curveItem.boundingRect().left(), curveItem.boundingRect().top()),(0.1,0.1),
            "BL",
            title = u"cos(%s)"%curveItem.title().text())
        self.plot.add_item(label)
        self.plot.replot()
        self.plot.do_autoscale()
        
        

    def fitCosSq(self):
        """ 
        Fit a cosin to the currently selected curve and plot the resulting fit function
        """
        if len(self.plot.get_selected_items()) == 0:
            l.warn("No curve selected to fit.")
            return False
        
        curveItem = self.plot.get_selected_items()[0]

        x = np.array(qwtArrayDoubleToList(curveItem.data().xData()))
        y = np.array(qwtArrayDoubleToList(curveItem.data().yData()))

        # fit using a cosin
        amplitude, frequency, phase, y0 , yFit= transdat.fitcos_squared(ndarrayToList(np.deg2rad(x)),ndarrayToList(y), fitY0 = True)
    
        self.plot.add_item(make.curve(ndarrayToList(x),ndarrayToList(yFit),
                                      color='r', 
                                      title=u"cos²fit(%s)"%curveItem.title().text()))
                                      
        label = make.label(u"""<i>cos²()-fit (%s)</i><br/>
            amplitude %.3e<br/>
            frequency %.3e°<br/>
            phase %.3e°<br/>
            offset y0 %.3e
            """%(curveItem.title().text(), amplitude, np.rad2deg(2*np.pi/frequency), np.rad2deg(phase), y0), 
            (curveItem.boundingRect().left(), curveItem.boundingRect().top()),(0.1,0.1),
            "BL",
            title = u"cos²(%s)"%curveItem.title().text())
        self.plot.add_item(label)
        self.plot.replot()
        self.plot.do_autoscale()


        
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
        self.comboBoxFile = QComboBox()
        self.comboBoxFile.setDisabled(1)
        self.groupBox = QComboBox()
        self.groupBox.setMinimumWidth(200)        
        self.groupBox.addItem("Data group")
        self.groupBox.setDisabled(1)
        self.fieldChannelBox = QComboBox()
        self.fieldChannelBox.setMinimumWidth(100)
        self.fieldChannelBox.addItem("Non-Unique Field Channel")
        self.fieldChannelBox.setDisabled(1)
        self.fieldBox = QComboBox()
        self.fieldBox.setMinimumWidth(75)
        self.fieldBox.setMaximumWidth(75)
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
        self.statusDisplay = QTextEdit()
        self.statusDisplay.setReadOnly(1)
        self.statusDisplay.setMinimumHeight(80)
        self.statusDisplay.setMaximumHeight(80)
        
        # Connect SIGNALs
        self.connect(buttonFile, SIGNAL('clicked()'), self.readFile)
        self.connect(self.buttonPlot, SIGNAL('clicked()'), self.plot)
        
        # Build Layout
        layout.addWidget(self.comboBoxFile,0,0,1,5)
        layout.addWidget(buttonFile,0,5)
        layout.addWidget(self.groupBox,1,0)
        layout.addWidget(self.fieldChannelBox,1,1)
        layout.addWidget(self.fieldBox,1,2)
        layout.addWidget(self.xChannelBox,1,3)
        layout.addWidget(self.yChannelBox,1,4)
        layout.addWidget(self.buttonPlot,1,5)
        layout.columnStretch(5)
        layout.addWidget(self.statusDisplay,3,0,1,6)        
        # Initialize store for TDMSfiles
        self.groupList = []
        self.ChannelList = []
        
        self.tdmsFiles = []     # holds all tdms files loaded in this session
        self.currentTdmsFile = None
                
        # Initialize plot widget
        self.widget = plotWidget(self)
        self.layout().addWidget(self.widget,2,0,1,6)
        self.buttonPlot.setEnabled(False)
        
        # Debuglevel for output in status display
        self.debugLevel = logging.DEBUG
        
        # Initialize Handler to write logging output to statusDisplay
        self.widgetLogger = widgetLogger(self.statusDisplay,self.debugLevel)
        l.addHandler(self.widgetLogger)        
        
    def readFile(self):
        """
        Read TDMS file from QFileDialog and add it to the list of TDMS files 
        and it's name to self.comboBoxFile
        Set this Tdms file to be the currently active one afterwards
        """
        filename = QFileDialog.getOpenFileName(self,u"Open file","",u"TDMS (*.tdms);;All files (*.*)")
        
        # Catch abortion of QFileDialog        
        if "" == filename:
            l.error(u"No file selected")
            return
            
        # Catch error in opening file  ~ TODO ~ could specify error?
        try:             
            self.tdmsFiles.append(nptdms.TdmsFile(filename))
        except:
            l.error(u"Error opening file")
            return
        
        self.comboBoxFile.addItem(filename)
        self.comboBoxFile.setEnabled(1)           
        
        self.comboBoxFile.setCurrentIndex(self.comboBoxFile.count()-1)
        
        if self.comboBoxFile.count() == 1:
            self.setCurrentTdmsFile(0)
            self.comboBoxFile.currentIndexChanged['int'].connect(self.setCurrentTdmsFile)


    def setCurrentTdmsFile(self,index):
        """
        Set the Tdms file in self.tdmsFiles at the specified index to be
        the currently used one and fill group and channel boxes appropriately)
        """
        l.debug("Setting current TDMS file to id %d of %d"%(index, len(self.tdmsFiles)))
        self.comboBoxFile.setCurrentIndex(index)
        self.currentTdmsFile = self.tdmsFiles[index]
        self.fillGroupBox(0)

        
    def resetChannelBoxes(self):
        """
        Clear channel combo boxes
        """        
        self.fieldChannelBox.clear()
        self.fieldChannelBox.addItem("No multiple fields in file")
        self.xChannelBox.clear()
        self.yChannelBox.clear()
        
        
    def fillGroupBox(self,index):
        """
        Fill comboBoxGroup with groups of the currently used TDMS file
        that contain "Read." in their name
        
        Parameters
        ----------
        index: int
            unused, for compatibility with signals
        """
        selectedGroupChannel = self.groupBox.currentIndex()

        self.groupBox.clear()
        for group in self.currentTdmsFile.groups():
            if group.startswith("Read."):
                self.groupBox.addItem(group)
        self.groupBox.setEnabled(1)
        l.debug("Filled group combo box with %d groups from %s"%(self.groupBox.count(),str(self.currentTdmsFile.groups())))
        
        # recall selected group
        self.groupBox.setCurrentIndex(selectedGroupChannel)
        self.fillChannelBoxes(0)

        # Fill channel boxes when user changes group
        self.groupBox.activated['int'].connect(self.fillChannelBoxes)     
        
    def fillChannelBoxes(self,index):
        """
        Populate self.xChannelBox and self.yChannelBox with the channels of the selected group
        If possible, uses the channels selected the previous time.
        
        Parameters
        ----------
        index: int
            unused, for compatibility with signals
        """
        l.debug("index %i" %index)
        self.channelList = self.currentTdmsFile.group_channels(str(self.groupBox.currentText()))
        
        # Store currently selected channels
        selectedFieldChannel = self.fieldChannelBox.currentIndex()
        selectedField = self.fieldBox.currentIndex()
        selectedXChannel = self.xChannelBox.currentIndex()
        selectedYChannel = self.yChannelBox.currentIndex()    

        self.resetChannelBoxes()

        # Fill with new channels                
        for channel in self.channelList:
            self.fieldChannelBox.addItem(re.search(r"'/'(.+)'",channel.path).group(1))
            self.xChannelBox.addItem(re.search(r"'/'(.+)'",channel.path).group(1))
            self.yChannelBox.addItem(re.search(r"'/'(.+)'",channel.path).group(1))

        # Enable boxes
        self.fieldChannelBox.setEnabled(1)
        self.xChannelBox.setEnabled(1)
        self.yChannelBox.setEnabled(1)
        self.buttonPlot.setEnabled(1)
        
        # Recalculate available fields when changing the field channel         
        self.fieldChannelBox.activated['int'].connect(self.fillFieldBox)
        
        # Recall selected channels
        self.fieldChannelBox.setCurrentIndex(selectedFieldChannel)
        self.fieldBox.setCurrentIndex(selectedField)
        self.xChannelBox.setCurrentIndex(selectedXChannel)
        self.yChannelBox.setCurrentIndex(selectedYChannel)

        # Fill field box once now after previous selected channels are restored
        self.fillFieldBox(self.fieldChannelBox.currentIndex())
        
     
    def fillFieldBox(self,index):
        """
        Populate field combo box with unique fields from channel selected in
        self.fieldChannelBox
        """
        # "No multiple fields" selected
        if index == 0:
            self.fieldBox.clear()
            self.fieldBox.setDisabled(1)
            return

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
