import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger
from mpi4py import MPI
from obspy.clients.filesystem.tsindex import Client as sql_client
from obspy import UTCDateTime

warnings.filterwarnings("ignore")

comm = MPI.COMM_WORLD  # pylint: disable=c-extension-no-member
size = comm.Get_size()
rank = comm.Get_rank()
station = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/station.txt', delimiter='|')
station = station[station['Longitude'] >= -164]
station['EndTime'] = station['EndTime'].fillna('2070-06-30T00:00:00')
station['StartTime'] = station['StartTime'].apply(lambda x: UTCDateTime(x)) 
station['EndTime'] = station['EndTime'].apply(lambda x: UTCDateTime(x)) 
start = UTCDateTime("2019-01-01T00:00:00")
end = UTCDateTime("2019-03-01T00:00:00")


OUTPUTS = Path(
    "/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_v1/data")
sq_client = sql_client("/mnt/scratch/jieyaqi/alaska/data.sqlite")


def remove_unused_list(process_list_this_rank_raw):
    # clean this rank
    filtered = []
    for index, net, sta, starttime, endtime in process_list_this_rank_raw:
        try:
            st = sq_client.get_availability(
                net, sta, "*", "*", starttime - 60, endtime + 60)
        except:
            filtered.append((index, net, sta, starttime, endtime))
        else:
            if len(st) > 0:
                filtered.append((index, net, sta, starttime, endtime))

    # collect all filtered
    filtered = comm.gather(filtered, root=0)
    # scatter
    if rank == 0:
        filtered_all = []
        for each in filtered:
            filtered_all.extend(each)
        filtered_all.sort()
        # reset index
        f = []
        index = 0
        for _, net, sta, starttime, endtime in filtered_all:
            f.append((index, net, sta, starttime, endtime))
            index += 1
        filtered_all = f

        filtered_all_splitted = np.array_split(filtered_all, size)
        total = len(filtered_all)
    else:
        filtered_all_splitted = None
        total = None
    res_each_rank = comm.scatter(filtered_all_splitted, root=0)
    total = comm.bcast(total, root=0)

    return res_each_rank, total


def get_process_list_this_rank(station):
    # get all array
    process_list = []

    index = 0
    staList = station.apply(lambda x: f'{x["Network"]}.{x["Station"]}', axis = 1).to_numpy()
    trunk = 10
    num = int(np.ceil((end - start)/ (60 * 60 * 24) / trunk))

    for each in staList:
        net, sta = each.split('.')
        for day in range(num):
            starttime = start+60*60*24*day*trunk
            endtime = start+60*60*24*(day*trunk+trunk) - 1e-6
            endtime = min(endtime, end)
            fname = OUTPUTS / \
                f"{net}.{sta}.{starttime.year}-{starttime.month}-{starttime.day}.mseed"
            if not fname.exists():
                process_list.append((index, net, sta, starttime, endtime))
                index += 1

    process_list_this_rank_raw = np.array_split(process_list, size)[rank]
    process_list_this_rank, total = remove_unused_list(
        process_list_this_rank_raw)

    return process_list_this_rank, total


def process_kernel(index, net, sta, starttime, endtime, total):
    try:
        st = sq_client.get_waveforms_bulk(
            [(net, sta, "*", "*", starttime - 60, endtime + 60)], None)
    except:
        logger.info(
                f"[{rank}]: {index}/{total} !Error accessing data: {net}.{sta} {starttime}->{endtime}")
        return

    if len(st) == 0:
        logger.info(
                f"[{rank}]: {index}/{total} !Error accessing data: {net}.{sta} {starttime}->{endtime}")
        return
    st.detrend("linear")
    st.detrend("demean")
    st.taper(max_percentage=0.002, type="hann")
    
    try:
        st.interpolate(sampling_rate=40)
    except ValueError:
        for tr in st:
            try:
                tr.interpolate(sampling_rate=40)
            except ValueError:
                st.remove(tr)
    st.merge(method=1, fill_value="latest")

    if len(st) == 0:
        logger.info(
                f"[{rank}]: {index}/{total} !Error processing data: {net}.{sta} {starttime}->{endtime}")
        return
    
    # mask to 0
    masks = []
    st.sort()
    for i in range(len(st)):
        if type(st[i].data) == np.ma.MaskedArray:
            masks.append(st[i].data.mask)
        else:
            masks.append(np.zeros(len(st[i].data), dtype=bool))

    for i in range(len(st)):
        st[i].data[masks[i]] = 0
    
    st.trim(starttime, endtime)

    # padding other channels
    channels = []
    for tr in st:
        channels.append(tr.stats.channel[2])

    if 'Z' not in channels:
        trz = st[0].copy()
        trz.data = np.zeros(len(trz.data))
        trz.stats.channel = st[0].stats.channel[:2]+'Z'
        st.append(trz)

    if 'E' not in channels and '1' not in channels:
        tre = st[0].copy()
        tre.data = np.zeros(len(tre.data))
        tre.stats.channel = st[0].stats.channel[:2]+'E'
        st.append(tre)

    if 'N' not in channels and '2' not in channels:
        trn = st[0].copy()
        trn.data = np.zeros(len(trn.data))
        trn.stats.channel = st[0].stats.channel[:2]+'N'
        st.append(trn)

    st.sort()
    if len(st) > 0:
        logger.info(
            f"[{rank}]: {index}/{total} {net}.{sta} {starttime}->{endtime}")
        fname = OUTPUTS / \
            f"{net}.{sta}.{starttime.year}-{starttime.month}-{starttime.day}.mseed"
        st.write(str(fname), format='MSEED')


def process(process_list_this_rank, total):
    for index, net, sta, starttime, endtime in process_list_this_rank:
        process_kernel(index, net, sta, starttime, endtime, total)


if __name__ == "__main__":
    process_list_this_rank, total = get_process_list_this_rank(station)
    process(process_list_this_rank, total)