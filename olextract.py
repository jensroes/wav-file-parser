#-------------------------------------------------------------------------------
# File Name   : onsetextr.py
# Description : This program detects the onset and offset of the speech for the
#               input wave files.
#-------------------------------------------------------------------------------
# Author      : Prateek Bansal
#-------------------------------------------------------------------------------
# Revised by Zenzi Griffin June 3, 2003 to skip initial times (250 ms) too early to
# be real response.
#-------------------------------------------------------------------------------
# Translation to Python: Jens Roeser
#-------------------------------------------------------------------------------

# Input parameters
path = '/media/jens/Roeser/CompareScripts' # Location of the wav files
fname = 'pythonlatency.txt' # name of output file with results
window_size = 10.0
start = 25 # 250ms start of onset estimation: to start estimatation of onset at the very start of the sounfile set parameter to 0


# Load packages
import os
from statistics import mean
import soundfile as sf
from scipy.signal import butter, lfilter, hamming


# Check if file exists already and iff remove file
file_name = path +'/' + fname
if os.path.exists(file_name):
    os.remove(file_name)

# Create output file
Fop  = open(file_name, 'a')
Fop.write("trial_id \t onset \t offset\n")

# Directory structure

files =  os.listdir(path)
wavfiles = []

for f in files:
    if f.endswith(".wav"):
        wavfiles.append(f)

nosfiles = len(wavfiles)

if nosfiles == 0:
    print "No wav files found"

filescell = sorted(wavfiles)

for icount in range(nosfiles):
    ft1 = str(filescell[icount])

    # Read wav file
    input_sig, Fs = sf.read(path + '/' + ft1)

    # Normalise the input signal
    input_sig = input_sig/max(input_sig)

    # High pass filtered at 100Hz to remove dc content and AC hum
    W1 = 200.0/Fs

    # Low pass filtered at 4Khz (4*10^3)
    W2 = 8000.0/Fs

    # Design the bandpass filter
    B, A = butter(10, [W2, W1], btype='band')

    # Filtered singal output
    filt_inpsig = input_sig

    # Clear the variables
    del W1, W2, input_sig

    # Normalise the filtered signal
    filt_inpsig = filt_inpsig/max(filt_inpsig)

    # Length of filtered data
    signal_length = len(filt_inpsig) - 1

    # WindowSize in samples
    win_samples = int(round((Fs*window_size)/1000.0))

    # Define the Hamming window
    ham_window = hamming(win_samples)

    energy = []
    for i in range(0, (signal_length - win_samples), win_samples):
        temp = filt_inpsig[i:(i+win_samples)]
        temp2 = temp*ham_window
        temp2 = abs(lfilter(B,A,temp2))
        energy.append(sum(temp2))

    # Clear variables
    del ham_window, win_samples, signal_length, temp, temp2

    # Energy threshold
    ITL = mean(energy) * .2 # lower threshold
    ITU = 5.0*ITL # upper threshold

    # Determination of end points
    N1 = 0.0 # start point initial estimate
    N2 = 0.0 # end point initial estimate

    duration = len(energy) - 1
    done = False

    # Estimation of the starting point based on energy considerations
    for m in range(start+1, duration):
        if energy[m] >= ITL and not done:
            for i in range(m+2, duration):
                if energy[i] < ITL:
                    break
                else:
                    if energy[i] >= ITU:
                        if not done:
                            N1 = i - (i == m)
                            done = True
                        break

    done = False

    # Estimation of end point based on energy considerations
    for m in range(duration,1,-1):
        if energy[m] >= ITL and not done:
            for i in range(m-2,1,-1):
                if energy[i] < ITL:
                    break
                else:
                    if energy[i] >= ITU:
                        if not done:
                            N2 = i + (i == m)
                            done = True
                        break

    warpRatio = round(len(filt_inpsig)/len(energy))
    N1_w = N1 * warpRatio
    N2_w = N2 * warpRatio

    # Evaluate speech_on and speech_off
    Speech_on = round((N1_w * 1000.0) / Fs)
    Speech_off = round((N2_w * 1000.0) / Fs)
    trial_id = str(ft1[0:len(ft1)-4])

    Fop.write("{}\t{}\t{}\n".format(trial_id, Speech_on, Speech_off))

    del ft1, Speech_on, Speech_off, N1, N1_w, N2, N2_w, warpRatio, energy, ITU, ITL

Fop.close()