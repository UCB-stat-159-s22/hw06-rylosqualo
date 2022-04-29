import numpy as np
import os
import fnmatch
import json
import h5py

def loaddata(filename, ifo=None, tvec=True, readstrain=True):
    """
    The input filename should be a LOSC .hdf5 file or a LOSC .gwf
    file.  The file type will be determined from the extenstion.  
    The detector should be H1, H2, or L1.
    The return value is: 
    STRAIN, TIME, CHANNEL_DICT
    STRAIN is a vector of strain values
    TIME is a vector of time values to match the STRAIN vector
         unless the flag tvec=False.  In that case, TIME is a
         dictionary of meta values.
    CHANNEL_DICT is a dictionary of data quality channels    
    """

    # -- Check for zero length file
    if os.stat(filename).st_size == 0:
        return None, None, None

    file_ext = os.path.splitext(filename)[1]    
    if (file_ext.upper() == '.GWF'):
        strain, gpsStart, ts, qmask, shortnameList, injmask, injnameList = read_frame(filename, ifo, readstrain)
    else:
        strain, gpsStart, ts, qmask, shortnameList, injmask, injnameList = read_hdf5(filename, readstrain)
        
    #-- Create the time vector
    gpsEnd = gpsStart + len(qmask)
    if tvec:
        time = np.arange(gpsStart, gpsEnd, ts)
    else:
        meta = {}
        meta['start'] = gpsStart
        meta['stop']  = gpsEnd
        meta['dt']    = ts

    #-- Create 1 Hz DQ channel for each DQ and INJ channel
    channel_dict = {}  #-- 1 Hz, mask
    slice_dict   = {}  #-- sampling freq. of stain, a list of slices
    final_one_hz = np.zeros(qmask.shape, dtype='int32')
    for flag in shortnameList:
        bit = shortnameList.index(flag)
        # Special check for python 3
        if isinstance(flag, bytes): flag = flag.decode("utf-8") 
        
        channel_dict[flag] = (qmask >> bit) & 1

    for flag in injnameList:
        bit = injnameList.index(flag)
        # Special check for python 3
        if isinstance(flag, bytes): flag = flag.decode("utf-8") 
        
        channel_dict[flag] = (injmask >> bit) & 1
       
    #-- Calculate the DEFAULT channel
    try:
        channel_dict['DEFAULT'] = ( channel_dict['DATA'] )
    except:
        print("Warning: Failed to calculate DEFAULT data quality channel")

    if tvec:
        return strain, time, channel_dict
    else:
        return strain, meta, channel_dict


def test_loaddata():
    eventname = 'GW150914'
    fnjson = "/home/jovyan/hw06-rylosqualo/BBH_events_v3.json"
    try:
        events = json.load(open(fnjson,"r"))
    except IOError:
        print("Cannot find resource file "+fnjson)
        print("You can download it from https://losc.ligo.org/s/events/"+fnjson)
        print("Quitting.")
        quit()

    # did the user select the eventname ?
    try:
        events[eventname]
    except:
        print('You must select an eventname that is in '+fnjson+'! Quitting.')
        quit()
    event = events[eventname]
    fn_H1 = event['fn_H1']              # File name for H1 data
    fn_L1 = event['fn_L1']              # File name for L1 data
    fn_template = event['fn_template']  # File name for template waveform
    fs = event['fs']                    # Set sampling rate
    tevent = event['tevent']            # Set approximate event GPS time
    fband = event['fband']              # frequency band for bandpassing signal
    try:
    # read in data from H1 and L1, if available:
        strain_H1, time_H1, chan_dict_H1 = loaddata(fn_H1, 'H1')
        strain_L1, time_L1, chan_dict_L1 = loaddata(fn_L1, 'L1')
    except:
        print("Cannot find data files!")
        print("You can download them from https://losc.ligo.org/s/events/"+eventname)
        print("Quitting.")
    quit()
    #test
    assert len(strain_H1) == 131072
