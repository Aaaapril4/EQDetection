import numpy as np
import pandas as pd
from obspy import UTCDateTime
from pyproj import Proj
from gamma.utils import association
import time


def filter_picks(picks: pd.DataFrame, ampP: float, ampS: float) -> pd.DataFrame:
    picks = picks[["net", "sta", "phase", "time", "amp"]]

    picksP = picks[picks["phase"] == "P"]
    picksP = picksP[picksP['amp'] >= ampP]

    picksS = picks[picks["phase"] == "S"]
    picksS = picksS[picksS['amp'] >= ampS]

    picks = pd.concat([picksP, picksS])
    picks.columns = ["network", "station", "type", "timestamp", "prob"]
    picks['id'] = picks.apply(lambda x: f'{x["network"]}.{x["station"]}..BH'.replace(' ', ''), axis = 1) # I use BH for all for convinience
    return picks[["id", "network", "station", "type", "timestamp", "prob"]]


def get_config() -> dict:
    '''
    Configuration for GaMMA
    '''
    config = {}
    config['initial_points'] = [1, 1, 2] # x, y, depth
    config["center"] = (-156, 55)
    config["xlim_degree"] = [-165, -147] # 1 or 2 degrees larger
    config["ylim_degree"] = [49, 61]
    config["starttime"] = UTCDateTime("20180101T00:00:00")
    config["endtime"] = UTCDateTime("20221231T23:59:59")
    config["z(km)"] = (0, 400)
    config["covariance_prior"] = [300, 300]
    config["vel"] = {"p": 6.0, "s": 6.0 / 1.75}
    config["method"] = "BGMM"
    config["oversample_factor"] = 20
    config["use_dbscan"] = True
    config["use_amplitude"] = False
    config["dbscan_eps"] = 30
    config["dbscan_min_samples"] = 3
    config["min_picks_per_eq"] = 10
    config["min_p_picks_per_eq"] = 3
    config["min_s_picks_per_eq"] = 3
    config["max_sigma11"] = 3
    config["max_sigma22"] = 3
    config["max_sigma12"] = 3
    config["ncpu"] = 20

    proj = Proj(f"+proj=sterea +lon_0={config['center'][0]} +lat_0={config['center'][1]} +units=km")
    config["dims"] = ['x(km)', 'y(km)', 'z(km)']
    xd = proj(longitude=config["xlim_degree"][0], latitude=config["ylim_degree"][0])
    yd = proj(longitude=config["xlim_degree"][1], latitude=config["ylim_degree"][1])
    config["x(km)"] = [xd[0], yd[0]]
    config["y(km)"] = [xd[1], yd[1]]
    config["bfgs_bounds"] = (
        (config["x(km)"][0] - 1, config["x(km)"][1] + 1),  # x
        (config["y(km)"][0] - 1, config["y(km)"][1] + 1),  # y
        (0, config["z(km)"][1] + 1),  # x
        (None, None),  # t
        )

    # uncomment if you choose to use 1D velocity model
    # Alaska model (averaged from Fan Wang's model)
    d, Vp, Vs = np.loadtxt("alaska.csv", usecols=(0, 1, 2), unpack=True, skiprows=1, delimiter=',')
    # PREM model
    # d, Vpv, Vph, Vsv, Vsh = np.loadtxt("PREM.csv", usecols=(1, 3, 4, 5, 6), unpack=True, skiprows=1)
    # Vp = np.sqrt((Vpv**2 + 4 * Vph**2)/5)
    # Vs = np.sqrt((2 * Vsv**2 + Vsh**2)/3)
    config["eikonal"] = {"xlim": config["x(km)"], 
                        "ylim": config["y(km)"], 
                        "zlim": config["z(km)"], 
                        "h": 1,
                        "vel": {"p": Vp, "s": Vs, "z": d}}
    return config, proj
    

picks = pd.read_csv('data/picks_raw.csv')
picks = filter_picks(picks, 0.5, 0.5)
picks['timestamp'] = picks['timestamp'].apply(lambda x: pd.Timestamp(x[:-1]))
picks = picks.sort_values("timestamp", ignore_index = True)

config, proj = get_config()

stations = pd.read_csv('data/stations.csv')
stations[["x(km)", "y(km)"]] = stations.apply(lambda x: pd.Series(proj(longitude=x.longitude, latitude=x.latitude)), axis=1)
stations["z(km)"] = stations["elevation(m)"].apply(lambda x: -x/1e3)

event_idx0 = 0  ## current earthquake index
assignments = []
start = time.time()
catalogs, assignments = association(
    picks, 
    stations, 
    config,
    event_idx0,
    method=config["method"],
)
end = time.time()
print(f"Association time: {(end - start)/60}")

event_idx0 += len(catalogs)
catalogs = pd.DataFrame(catalogs, columns=["time"]+config["dims"]+["magnitude", "sigma_time", "sigma_amp", "cov_time_amp",  "event_index", "gamma_score"])
catalogs[["longitude","latitude"]] = catalogs.apply(lambda x: pd.Series(proj(longitude=x["x(km)"], latitude=x["y(km)"], inverse=True)), axis=1)
catalogs["depth(m)"] = catalogs["z(km)"].apply(lambda x: x*1e3)
assignments = pd.DataFrame(assignments, columns=["pick_index", "event_index", "gamma_score"])
picks = picks.join(assignments.set_index("pick_index")).fillna(-1).astype({'event_index': int})
picks = picks.merge(stations, "outer", on="id")
picks = picks.dropna()

with open('/mnt/scratch/jieyaqi/alaska/manual_pick_test/catalogs_gamma_Alaska.csv', 'w') as fp:
    catalogs.to_csv(fp, index=False, 
                float_format="%.3f",
                date_format='%Y-%m-%dT%H:%M:%S.%f')

with open('/mnt/scratch/jieyaqi/alaska/manual_pick_test/picks_gamma_Alaska.csv', 'w') as fp:
    picks.to_csv(fp, index=False, 
                date_format='%Y-%m-%dT%H:%M:%S.%f')

