import pandas as pd
from pathlib import Path
from obspy import UTCDateTime

basedir = '/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_v1'
station = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/station.txt', delimiter='|')
staList = list(station.apply(lambda x: f'{x["Network"]}.{x["Station"]}', axis = 1))
starttime = UTCDateTime("2018-01-01T00:00:00")
endtime = UTCDateTime("2019-02-28T23:59:59")


def generate_csv(datadir, output):
    df = pd.DataFrame()

    for sta in staList:
        sta_start = UTCDateTime.now()
        sta_end = UTCDateTime('1970-01-01')
        flag = 0
        for mseed in datadir.glob(f'{sta}.*'):
            flag = 1
            net, st, start, _ = mseed.name.split('.')
            start = UTCDateTime(start)
            end = min(start + 10 * 24 * 60 * 60, endtime)
            if start < sta_start:
                sta_start = start
            if end > sta_end:
                sta_end = end
        
        if flag != 0:
            statime = pd.Series({
                'network': net,
                'station': st,
                'start_time': sta_start,
                'end_time': sta_end
            }).to_frame().T
            df = pd.concat([df, statime], ignore_index=True)

    df.to_csv(output, sep=",", index=False, 
        date_format='%Y-%m-%dT%H:%M:%S.%f')
    return
    
if __name__ == '__main__':
    for num in range(1, 7):
        data = Path(f"{basedir}/data{num}")
        output = Path(basedir) / f'statime{num}.csv'
        generate_csv(data, output)