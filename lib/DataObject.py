# -*- coding: utf-8 -*-
"""
Created on Wed Jul 23 10:32:51 2014

"""
import transportdata as transdat
import numpy as np 

import logging
logging.basicConfig()
l = logging.getLogger(__name__)
l.setLevel(logging.DEBUG)

class DataObject():
    """
    Creates a data object containing x and y data. Data can be processed by
    adding operations to a queue by simply calling the processing member functions.
    TODO: Add list of supported operations to the documentation here.
    
    Process the data by calling self.processData(). The processed data then is 
    returned and stored in self.xCalc() and self.yCalc()

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
    def __init__(self,x,y, label = None, path = None, group = None, paramChannel = None, param = None, xChannel = None, yChannel = None):
        self.x = x
        self.y = y
        self.xCalc = np.array(x)
        self.yCalc = np.array(y)
        self.label = label

        self.path = unicode(path)
        self.group = group
        self.paramChannel = paramChannel
        self.param = param
        self.xChannel = xChannel
        self.yChannel = yChannel
        
        self.operations = []
        self.operationParameters = []
        self.isUpDownData = True # whether the currently calculated data consists of an up and down sweep

    def __str__(self):
        return """Data Object "%s" for data in file '%s'
    Group: '%s'
    Parametrized according to '%s' (selected '%s')
    xChannel: '%s' (%d long)
    yChannel: '%s' (%d long)
    #Operations: %d"""%(self.label, self.path, self.group, self.paramChannel, self.param, self.xChannel, len(self.x), self.yChannel, len(self.y), len(self.operations))        
        
    def _deltaMethod(self, method):
        """
        method : int(0-4)
            0: no delta method [n] (default)
            1: uneven indexed raw data [2n-1]
            2: even indexed raw data [2n]
            3: difference ([2n-1]-[2n])/2
            4: sum ([2n-1]+[2n])/2
        """
        x = self.xCalc
        y = self.yCalc
        
        if method == 0:
            # plain raw data
            pass
        elif method == 1:
            # odd raw data values
            x = transdat.separateAlternatingSignal(x)[0]
            y = transdat.separateAlternatingSignal(y)[0]
        elif method == 2:
            # even raw data values
            x = transdat.separateAlternatingSignal(x)[1]
            y = transdat.separateAlternatingSignal(y)[1]
        elif method == 3:
            # difference of odd - even values
            x = transdat.separateAlternatingSignal(x)[0]
            y = transdat.separateAlternatingSignal(y)[0] -  transdat.separateAlternatingSignal(y)[1]
        elif method == 4:
            # difference of odd - even values
            x = transdat.separateAlternatingSignal(x)[0]
            y = transdat.separateAlternatingSignal(y)[0] +  transdat.separateAlternatingSignal(y)[1]

        self.xCalc = x
        self.yCalc = y
        
    def deltaMethod(self, method):
        """
        Queue delta method processing.
        
        Parameters
        ----------
        method : int(0-4)
            0: no delta method [n] (default)
            1: uneven indexed raw data [2n-1]
            2: even indexed raw data [2n]
            3: difference ([2n-1]-[2n])/2
            4: sum ([2n-1]+[2n])/2
        """
        if method:
            self.operations.append(self._deltaMethod)
            self.operationParameters.append({'method': method})


    def _averageUpDown(self):
        """
        Average up and down sweep
        
        and mark data as being averaged (for e.g. symmetrization)
        """
        if not self.isUpDownData:
            raise Exception("Averaging up-down-sweep only makes sense if there's an up- and down-sweep. The function can only be called once.")
        self.xCalc = transdat.averageUpDownSweep(self.xCalc)
        self.yCalc = transdat.averageUpDownSweep(self.yCalc)                    
        self.isUpDownData = False
        
    def averageUpDown(self):
        """
        Queue averaging an up and down sweep (queue this only once)
        """
        self.operations.append(self._averageUpDown)
        self.operationParameters.append({}) # add empty to maintain index sync
                                            # w/ self.operations

    def _normalize(self, method):
        """
        method : int(0-2)
            0: no normalization (default)
            1: normalize y to min(y)
            2: normalize y to max(y)
        """
        if 0 == method:
            pass
        elif 1 == method:
            # normalize by min(y)
            self.yCalc = self.yCalc/np.min(self.yCalc)
        elif 2 == method:
            # normalize by max(y)
            self.yCalc = self.yCalc/np.max(self.yCalc)

    def normalize(self, method):
        """
        Queue normalizing the y-data according to method
        
        Parameters
        ----------
        method : int(0-2)
            0: no normalization (default)
            1: normalize y to min(y)
            2: normalize y to max(y)
        """
        if method:
            self.operations.append(self._normalize)
            self.operationParameters.append({'method': method})


    def _symmetrize(self, method, symm_step = None, symm_center = None):
        """
        method : int(0-2)
            0: no symmetrization (default)
            1: symmetrization
            2: antisymmetrization
        """
        if ((not symm_step == None and not symm_center == None)
            or (symm_step == None and symm_center == None)):
                raise Exception("Provide either a center of symmetry (symm_center) or a symmetry step (symm_step).")
            
        x = self.xCalc
        y = self.yCalc
        if method and symm_step != None and self.isUpDownData:
            #admr data        
            # only regard one half of the data for finding the period
            stepIdx = int(np.abs((np.abs(x[0:int(len(x))+1/2]-0)).argmin() 
                       - (np.abs(x[0:int(len(x)/2+1)]-symm_step)).argmin()))
            stepWidth = (x[(np.abs(x[0:int(len(x)/2+1)]-0)).argmin()] 
                        - x[np.abs(x[1:int(len(x)/2+1)]-symm_step).argmin()+1])
            l.debug("(Anti-)Symmetrizing admr data with period %d (val:%f)"%(stepIdx,np.abs(stepWidth)))
            
            if 1 == method: # symmetrize
                y = transdat.symmetrizeSignalUpDown(y,stepIdx)
                x = x[0:len(y)]
            elif 2 == method: #antisymmetrize
                y = transdat.antiSymmetrizeSignalUpDown(y,stepIdx)
                x = x[0:len(y)]
        elif method and  symm_step != None and not self.isUpDownData:
            #admr data where up and down sweep are already averaged
            stepIdx = int(np.abs((np.abs(x-0)).argmin() 
                       - (np.abs(x-symm_step)).argmin()))
            stepWidth = (x[(np.abs(x-0)).argmin()] 
                        - x[np.abs(x-symm_step).argmin()+1])
            l.debug("(Anti-)Symmetrizing admr data with period %d (val:%f)"%(stepIdx,np.abs(stepWidth)))
            
            if 1 == method: # symmetrize
                y = transdat.symmetrizeSignal(y,stepIdx)
                x = x[0:len(y)]
            elif 2 == method: #antisymmetrize
                y = transdat.antiSymmetrizeSignal(y,stepIdx)
                x = x[0:len(y)]
        elif method and symm_center != None:
            centerIdx = (np.abs(x-symm_center)).argmin()
            l.debug("(Anti-)Symmetrizing data of len %d around index %d (val: %f)"%(len(x),centerIdx, x[centerIdx]))
            # R(H) data
            if 1 == method: # symmetrize
                y = transdat.symmetrizeSignalZero(y,centerIdx)
                x = x[0:len(y)][::-1]
            elif 2 == method: # symmetrize
                y = transdat.antiSymmetrizeSignalZero(y,centerIdx)
                x = x[0:len(y)][::-1]
        
        self.xCalc = x
        self.yCalc = y

    def symmetrize(self, method, symm_step = None, symm_center = None):
        """
        Queue symmetrizing data see doc/symmetrizing for conventions and algorithm (FIXME)
        
        Parameters
        ----------
        method : int(0-2)
            0: no symmetrization (default)
            1: symmetrization
            2: antisymmetrization
        """
        if method:
            if ((not symm_step == None and not symm_center == None)
                or (symm_step == None and symm_center == None)):
                    raise Exception("Provide either a center of symmetry (symm_center) or a symmetry step (symm_step).")
            
            self.operations.append(self._symmetrize)
            self.operationParameters.append({'method': method, 'symm_step': symm_step, 'symm_center': symm_center})

        
    def _offsetCorrection(self, method, offset = None):
        """
        switchOffset : int(0-4)
            0   -> no offset correction (default)
            1   -> subtracts min(y)
            2   -> subtracts max(y)
            3   -> subtracts mean(y)
            4   -> subtracts value defined in valueOffset
        offset : double 
            custom value to subtract from the data (if switchOffset = 4) (default = None)
        """
        if 0 == method:
            pass
        elif 1 == method:
            # subtract min(y)
            offset = np.min(self.yCalc)
        elif 2 == method:
            # subtract max(y)
            offset = np.max(self.yCalc)
        elif 3 == method:
            # subtract mean(y)
            offset = np.mean(self.yCalc)

        self.yCalc = self.yCalc-offset

    def offsetCorrection(self, method, offset = None):
        """
        Queue substracting the offset
        
        Parameters
        ----------
        switchOffset : int(0-4)
            0   -> no offset correction
            1   -> subtracts min(y)
            2   -> subtracts max(y)
            3   -> subtracts mean(y)
            4   -> subtracts value defined in valueOffset
        offset : double 
            custom value to subtract from the data (if switchOffset = 4) (default = None)
        """
        if method:
            self.operations.append(self._offsetCorrection)
            self.operationParameters.append({'method': method, 'offset': offset})
        
        
    def processData(self):
        """
        Apply queued operations
        
        Returns
        ----------
        xCalc : np.ndarray()
            x-channel of the processed data

        yCalc : np.ndarray()
            y-channel of the processed data
        """
        self.xCalc = np.array(self.x)
        self.yCalc = np.array(self.y)        
        
        for idx, operation in enumerate(self.operations):
            operation(**self.operationParameters[idx])
            
        return self.xCalc, self.yCalc
        
    def operationsToString(self):
        opString = ""
        for idx, operation in enumerate(self.operations):
            opString += str(operation.__name__) + ":\n"
            opString += "   %s"%(self.operationParameters[idx])
        return opString
            
    def saveASCII(self, fname):
        header = str(self) + self.operationsToString()
        np.savetxt(fname, np.transpose((self.xCalc, self.yCalc)), header = header)
        