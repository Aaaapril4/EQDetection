# import pandas as pd
from pathlib import Path
from obspy import UTCDateTime
import numpy as np
import sys

phase_frac = float(sys.argv[1]) # percentage of picks to do relocation
phases = sys.argv[2] # path to phases file
cats = sys.argv[3] # path to catalog file
outdir = Path(sys.argv[4]) # output directory
OUTPUTS = outdir / "phase.dat"

phase_station, phase_type, phase_time, phase_eventid = np.loadtxt(phases, usecols = [0, 1, 2, 4], dtype = str, unpack=True, delimiter=',', skiprows=1)
cat_time, cat_eventid, cat_longitude, cat_latitude, cat_depth = np.loadtxt(cats, usecols = [0, 8, 10, 11, 12], dtype = str, unpack=True, delimiter=',', skiprows=1)
phase_station = np.array([x.split('.')[1] for x in phase_station])
phase_eventid = phase_eventid.astype(float)
cat_eventid = cat_eventid.astype(float)
cat_longitude = cat_longitude.astype(float)
cat_latitude = cat_latitude.astype(float)

# template for events and picks
ev = "# {year} {month} {day} {hour} {minute} {second:.3f} {lat} {lon} {depth:.3f} 0 0 0 0 {id}\n"
pick = "{sta} {traveltime:.3f} 1 {phase}\n"

with open(OUTPUTS, 'w') as f:
    for i in range(len(cat_time)):
        if cat_longitude[i] < -165 or cat_longitude[i] > -147 or cat_latitude[i] < 49 or cat_latitude[i] > 61:
            continue
        otime = UTCDateTime(cat_time[i])
        current_eventid = cat_eventid[i]
        f.write(ev.format(
            year = otime.year,
            month = otime.month,
            day = otime.day,
            hour = otime.hour,
            minute = otime.minute,
            second = otime.second + otime.microsecond / 1e6,
            lat = cat_latitude[i],
            lon = cat_longitude[i],
            depth = float(cat_depth[i])/1000,
            id = int(current_eventid)
        ))

        mask = (phase_eventid == current_eventid)
        evphase_type = phase_type[mask]
        evphase_station = phase_station[mask]
        evphase_time = phase_time[mask]
        select_index = np.random.choice(range(len(evphase_type)), size = int(np.ceil(len(evphase_type) * phase_frac)), replace = False)

        for i in select_index:
            f.write(pick.format(
                sta = evphase_station[i],
                traveltime = UTCDateTime(evphase_time[i]) - otime,
                phase = evphase_type[i]
            ))