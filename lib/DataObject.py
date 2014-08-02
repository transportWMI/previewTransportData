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
    def __init__(self,x,y, label = None):
        l.info("Adding new data set with len(x) = %d"%np.size(x))
        self.x = x
        self.y = y
        self.xCalc = x
        self.yCalc = y
        self.label = label
        
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