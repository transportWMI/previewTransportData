# -*- coding: utf-8 -*-
"""
Created on Mon Jun 23 13:32:51 2014

Shared functions for processing transport measurement data.

@author: hannes.maierflaig
"""

import numpy as np
import scipy.optimize as optimize
import scipy.fftpack as fftpack

import logging
logging.basicConfig()
l = logging.getLogger(__name__)
l.setLevel(logging.DEBUG)

def symmetrizeSignalZero(y, idx = None):
    """
    Dischard antisymmetric (around center index or around idx) part by 
    taking the sum of the signal at x[idx_centre +n] and x[idx_centre -n]
    
    Parameters
    ----------
    y : array_like 
        numpy array or list of data values to anti symmtetrize
    idx : scalar
        index of center to symmetrize around if ommitted len(y)/2 is taken as idx
    
    Returns
    ----------
    y_symmetrized : ndarray
        numpy array of dimension size(y)/2 of the symmetrized data
    """
    y = np.array(y)
    if not np.size(y)%2:
        raise Exception("Data needs to have an uneven number of elements if no center index (idx) is provided")
    if not idx:
        idx = np.size(y)/2
        idx_end = np.size(y)
    else:
        idx_end = min((np.size(y), idx*2))
        
    y = (y[0:idx] + y[idx+1:idx_end][::-1])/2
    return y


def antiSymmetrizeSignalZero(y, idx = None):
    """
    Dischard symmetric (around center index or around idx) part by 
    taking the difference of the signal at x[idx_centre +n] and x[idx_centre -n]
        
    Parameters
    ----------
    y : array_like 
        numpy array or list of data values to anti symmtetrize
    idx : scalar
        index of center to symmetrize around if ommitted len(y)/2 is taken as idx
    
    Returns
    ----------
    y_symmetrized : ndarray
        numpy array of dimension size(y)/2 of the antisymmetrized data
    """
    y = np.array(y)
    if not np.size(y)%2:
        raise Exception("Data needs to have an uneven number of elements if no center index (idx) is provided")
    if not idx:
        idx = np.size(y)/2
        idx_end = np.size(y)
    else:
        idx_end = min((np.size(y), idx*2))
        
    y = (y[0:idx] - y[idx+1:idx_end][::-1])/2
    return y
    
    
def antiSymmetrizeSignal(y, symmetryStep):
    """    
    Dischard symmetric (around center index or around idx) part of a signal by 
    taking the difference of the signal at x[idx_centre +n] and x[idx_centre +n + symmetry_step]
    get your corresponding x data as x[0:len(y)/]
                
    Parameters
    ----------
    y : array_like 
        numpy array or list of data values to anti symmtetrize
    symmetryStep : scalar
        expected symmetry of the signal at x[n] occurs at x[n+symmetryStep]
    
    Returns
    ----------
    y_symmetrized : ndarray
        numpy array of dimension size(y)/2 of the antisymmetrized data
    """
    y = np.array(y)
        
    s = np.zeros(len(y)/2)
    for idx in range(0, len(s)):
        # (positive field - negative field)/2
        s[idx] = (y[symmetryStep+idx] - y[symmetryStep-idx])/2
        #s[idx] = (y[idx] - y[idx+symmetryStep])/2.-(y[0] - y[0+symmetryStep])/2.
    return s


def symmetrizeSignal(y, symmetryStep):
    """
    Dischard antisymmetric (around center index or around idx) part of a signal by 
    taking the sum of the signal at x[idx_centre +n] and x[idx_centre +n + symmetry_step].
    
    Get your corresponding x data as x[0:len(y)/]
    
    Parameters
    ----------
    y : array_like 
        numpy array or list of data values to anti symmtetrize
    symmetryStep : scalar
        expected symmetry of the signal at x[n] occurs at x[n+symmetryStep]
    
    Returns
    ----------
    y_symmetrized : ndarray
        numpy array of dimension size(y)/2 of the symmetrized data
    """
    y = np.array(y)
        
    s = np.zeros(len(y)-symmetryStep)
    for idx in range(0, len(s)):
        s[idx] = (y[idx] + y[idx+symmetryStep])/2.-(y[0] + y[0+symmetryStep])/2.
    return s


def symmetrizeSignalUpDown(y, symmetryStep):
    """
    Symmetrize a signal that is recorded as an up and down sweep by calculating
    the cross sum between up and down sweep of values shifted by symmetry step.
    
    Get the corresponding x data as averageUpDownSweep(x).
        
    Parameters
    ----------
    y : array_like 
        numpy array or list of data values to anti symmtetrize
    symmetryStep : scalar
        expected symmetry of the signal at x[n] occurs at x[n+symmetryStep]
    
    Returns
    ----------
    y_symmetrized : ndarray
        numpy array of dimension size(y)/2 of the symmetrized data
    """
    y=np.array(y)
 
    yU = y[0:len(y)/2] # up sweep (for the sake of the argument)                    
    yD = y[len(y)/2:][::-1] # down sweep w/ same axis
    
    
    sL = np.zeros(2*symmetryStep)
    for idx in range(0, symmetryStep):
        sL[idx] = (yU[idx] + yD[idx+symmetryStep])/2
    for idx in range(symmetryStep,2*symmetryStep):
        sL[idx] = (yU[idx] + yU[idx-symmetryStep])/2.
    return sL
    
    

def antiSymmetrizeSignalUpDown(y, symmetryStep):
    """
    Antisymmetrize a signal that is recorded as an up and down sweep by calculating
    the cross difference between up and down sweep of values shifted by symmetry step.
    
    Get the corresponding x data as averageUpDownSweep(x).
    
    Parameters
    ----------
    y : array_like 
        numpy array or list of data values to anti symmtetrize
    symmetryStep : scalar
        expected symmetry of the signal at x[n] occurs at x[n+symmetryStep]
    
    Returns
    ----------
    y_symmetrized : ndarray
        numpy array of dimension size(y)/2 of the antisymmetrized data
    """
    y=np.array(y)

    yU = y[0:len(y)/2] # up sweep (for the sake of the argument)                    
    yD = y[len(y)/2:][::-1] # down sweep w/ same axis
    
    sL = np.zeros(2*symmetryStep)
    for idx in range(0, symmetryStep):
        sL[idx] = (yU[idx] - yD[idx+symmetryStep])/2
    for idx in range(symmetryStep,2*symmetryStep):
        sL[idx] = (yU[idx] - yU[idx-symmetryStep])/2.
    return sL
    
def separateAlternatingSignal(x):
    """
    Separates each 2nd element of an array into two array

    Returns    
    ----------
    separated_signal : list of two arrays (x[2n], x[2n-1])
    """
    if np.size(x)%2:
        x = x[:-1]
        l.warn("""Data does not have an even number of elements. Dropping last datapoint. 
        Maybe the data has not been recorded using a delta method?""")
    return np.array(x[0::2]), np.array(x[1::2])

    
def averageUpDownSweep(x, num=1):
    """
    Calculate x[center+n] + x[center-n] of a signal thereby data recorded as up,
    then down sweep can be averaged.
       
    Parameters
    ----------
    x : data (list or numpy array) to average
    num : apply algorithm num times to average more than once (default: 1)
    
    Returns    
    ----------
    x_averaged : numpy array of the averaged data
    """
    x = np.array(x)
    for i in range(num):
        x = (x[0:np.size(x)/2] + x[::-1][0:np.size(x)/2])/2
    return x
    
    
def preprocessTransportData(field, angle, U, I = None, fields = None, n_angle_points = None, delta_method = True):
    """
    Parse transport rotational data that has been recorded at various fields
    and return a dict that contains the data for each field value.
    
    Parameters
    ----------
    field : tuple
        Field values as they are recorded in the experiment (2 for each angle
        if the delta method is applied, otherwise one per angle)
        Alternatively (tuple) of unique field points in conjunction w/ n_angle_points
        to disable automatic detection.
    angle : tuple
        Field values as they are recorded in the experiment (each angle twice
        if the delta method is applied)
    U : tuple
        Recorded Voltage. If the delta method is applied and I is not specified
        it is assumed that the first entry corresponds to a positive Voltage
    I : tuple (optional)
        Applied current for each sweep point. If provided, the U/I is evaluated
        at each sweep point instead and R = U/I is returned instead of U
    n_angle_points: scalar (optional)
        Disable automatic detection of angle points, for aborted measurements
    
    Returns
    ----------
    data : dict of {dict for each field}
        field : 
            unique field value
        angle : 
            unique angles (0,1,2,...2,1,0 for up-down sweep, not 0,0,1,1,… though)
        I : 
            None, if I is not specified, [min(I), max(I)] of the provided I values instead
        signal_diff :  only if delta_method == True
            signal[2n-1]-signal[2n]
        signal_sum : only if delta_method == True
            signal[2n-1]+signal[2n]        
        signal_raw1 : only if delta_method == True
            signal[2n-1]
        signal_raw2 : only if delta_method == True
            signal[2n] :
        signal : only if delta_method == False
            signal[:]
        signal specifies U for the field "field" in the dict if function 
        argument I is not provided . otherwise, if I is provided, signal specifies R = U/I

        
    Usage example
    ----------    
    Unpacking a dict for the values
    
    >>> preprocessTransportData(**{"fields": ..., "angle": ..., "I": .., "U": ...}, deltaMethod = False)
    
    
    Or directly from a tmds file:
    
    >>> from nptmds import TdmsFile
    >>> tdms = TdmsFile("2014-06-25/YY84/2014-06-23-YY84-A02-admr_300K.tdms")
    >>> field = tdms.channel_data("Read.K2400_long_oopj", "IPS.TargetField")
    >>> angle =  tdms.channel_data("Read.K2400_long_oopj", "owis.Angle (deg)")
    >>> structuredData  = preprocessTransportData(field, angle, 
        tdms.channel_data("Read.K2400_long_oopj", "K2400U"))
    
    """        
    
    l.debug("Loading data for dim(field) = %d,  dim(angle) = %d,  dim(U) = %d"%(len(field), len(angle), len(U)))
    if np.size(field) == np.size(angle) and n_angle_points == None:
        # automatically calculate field points
        uniqueFields, uniqueFieldStartIdx = np.unique(field, return_index=True)
        l.debug("found unique fields in data: ")
        l.debug(uniqueFields)
    elif n_angle_points:
        # get field indices by user provided parameters
        uniqueFields = field
        uniqueFieldStartIdx = np.zeros_like(uniqueFields, dtype=np.int)
        for idx, _ in enumerate(uniqueFields):
            uniqueFieldStartIdx[idx] = idx*n_angle_points
    else: 
        l.error("There's not a field value recorded for each angle or .")
            
    # sort fields by index not by field value (so the last field is also the last measurement)
    uniqueFields = uniqueFields[np.argsort(uniqueFieldStartIdx)]
    uniqueFieldStartIdx = np.sort(uniqueFieldStartIdx)
    
    data = []
    for idx, uniqueField in enumerate(uniqueFields):
        l.debug("Parsing data for field %.2f T."%uniqueField)
        if idx == np.size(uniqueFields)-1:
            # last rotation might be unfinished, just taking the remaining points
            if not (uniqueFieldStartIdx[idx]-np.size(angle)-1)%2 and delta_method == True:
                stopIdx = np.size(angle)-1
                l.warn("Ditching last datapoint of the last rotation in order to be able to symmetrize")
            else:
                stopIdx = np.size(angle)
            fieldRange = np.arange(uniqueFieldStartIdx[idx],stopIdx)
        else:
            # complete measurements
            fieldRange = np.arange(uniqueFieldStartIdx[idx],uniqueFieldStartIdx[idx+1], 
                                   np.sign(uniqueFieldStartIdx[idx+1]-uniqueFieldStartIdx[idx]))
        l.debug("It's field index range is (%d, %d)", fieldRange[0], fieldRange[-1])

        if I:
            signal = U/I # return R instead of U
            returnI = [min(I), max(I)] # return the "absolute" of I in the dict
        else:
            signal = U # return plain voltage
            returnI = None    


        angle = np.array(angle)  
        if delta_method:
            data.append({
                "field": uniqueField,
                "angle": angle[fieldRange][0::2],
                "I": returnI,
                "signal_diff": signal[fieldRange][0::2]-signal[fieldRange][1::2],
                "signal_sum":  signal[fieldRange][0::2]+signal[fieldRange][1::2],
                "signal_raw1": signal[fieldRange][0::2],
                "signal_raw2": signal[fieldRange][1::2]
                })
        else:
            data.append({
                "field": uniqueField,
                "angle": angle[fieldRange],
                "I": returnI,
                "signal": signal[fieldRange]
                })
        
    return data 
    
def fitcos(x, y, fitY0 = False, guess = None):
    """
    Fit a cosin to the date in x and y.
    """
    def cos(x, amplitude, frequency, phase):
        return amplitude * np.cos(frequency * x + phase)   
    def cos_y0(x, amplitude, frequency, phase, y0):
        return amplitude * np.cos(frequency * x + phase) + y0    

    x = np.array(x)
    y = np.array(y)    
    if not guess:       
        # fourier transform to find guess value for frequency
        yhat = fftpack.rfft(y)
        idx = (yhat**2).argmax()
        freqs = fftpack.rfftfreq(np.size(x), d = (x[0]-x[1])/(2*np.pi))
        frequency0 = freqs[idx]
        if frequency0 == np.Inf or frequency0 == 0:
            frequency0 = 0.001
        # maximum to find guess for amplitude
        amplitude0 = np.abs(max(y)-min(y))/2
        y00 = (max(y)-min(y))/2+min(y)
        phase0 = 0.
    else:
        amplitude0 = guess[0]
        frequency0 = guess[1]
        phase0 = guess[2]
        if fitY0:
            y00 = guess[3]
    l.debug("Fit cosin. Guessing: Amplitude %.3e, Frequency %.3e, Phase %.3e, Offset y0 %.3e"%(amplitude0, frequency0, phase0, y00))
    
    if fitY0:
        guess = [amplitude0, abs(frequency0), phase0, y00]
        (amplitude, frequency, phase, y0), pcov = optimize.curve_fit(
            cos_y0,
            x, y,
            guess)
        yFit = cos_y0(x, amplitude, frequency, +phase, y0)
        return (amplitude, frequency, phase, y0, yFit)
    else:
        guess = [amplitude0, abs(frequency0), phase0]
        (amplitude, frequency, phase), pcov = optimize.curve_fit(
            cos,
            x, y,
            guess)
        yFit = cos(x, amplitude, frequency, +phase)        
        return (amplitude, frequency, phase, 0, yFit)
        
        
def fitcos_squared(x, y, fitY0 = False, guess = None, debug=False):
    """ untested, probably not working correctly"""
    def cossq(x, amplitude, frequency, phase):
        return amplitude * np.cos(frequency * x + phase)**2   
    def cossq_y0(x, amplitude, frequency, phase, y0):
        return amplitude * np.cos(frequency * x + phase)**2 + y0    

    x = np.array(x)
    y = np.array(y)    
    if not guess:       
        # fourier transform to find guess value for frequency
        yhat = fftpack.rfft(y)
        idx = (yhat**2).argmax()
        freqs = fftpack.rfftfreq(np.size(x), d = (x[0]-x[1])/(2*np.pi))
        frequency0 = freqs[idx]
        if frequency0 == np.Inf:
            frequency0 = 0.001
        # maximum to find guess for amplitude
        amplitude0 = np.abs(max(y)-min(y))/2
        y00 = (max(y)-min(y))/2+min(y)
        phase0 = 0.
    else:
        amplitude0 = guess[0]
        frequency0 = guess[1]
        phase0 = guess[2]
        if fitY0:
            y00 = guess[3]
    print("Fit cosin squared. Guessing: Amplitude %.3e, Frequency %.3e, Phase %.3e, Offset y0 %.3e"%(amplitude0, frequency0, phase0, y00))
  
    if fitY0:
        guess = [amplitude0, abs(frequency0), phase0, y00]
        (amplitude, frequency, phase, y0), pcov = optimize.curve_fit(
            cossq_y0,
            x, y,
            guess)
        yFit = cossq_y0(x, amplitude, frequency, +phase, y0)
        return (amplitude, frequency, phase, y0, yFit)
    else:
        guess = [amplitude0, abs(frequency0), phase0]
        (amplitude, frequency, phase), pcov = optimize.curve_fit(
            cossq,
            x, y,
            guess)
        yFit = cossq(x, amplitude, frequency, +phase)
        return (amplitude, frequency, phase, 0, yFit)
        