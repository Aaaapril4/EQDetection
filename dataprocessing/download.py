import obspy
from obspy.clients.fdsn.mass_downloader import RectangularDomain, Restrictions, MassDownloader
from obspy.clients.fdsn import Client
client = Client("IRIS")

# This domain is for Alaska Peninsula, you may have a smaller region
domain = RectangularDomain(minlatitude=50, maxlatitude=60,
                           minlongitude=-166, maxlongitude=-148)

restrictions = Restrictions(
    # Get data for a whole year.
    starttime=obspy.UTCDateTime(1989, 12, 8),
    endtime=obspy.UTCDateTime(1989, 12, 9),
    # Chunk it to have one file per day.
    chunklength_in_sec=86400 * 10,
    # Considering the enormous amount of data associated with continuous
    # requests, you might want to limit the data based on SEED identifiers.
    # If the location code is specified, the location priority list is not
    # used; the same is true for the channel argument and priority list.
    network="SH", 
    station="BAL", 
    location="", 
    channel="EH*",
    # The typical use case for such a data set are noise correlations where
    # gaps are dealt with at a later stage.
    reject_channels_with_gaps=False,
    # Same is true with the minimum length. All data might be useful.
    minimum_length=0.0,
    # Guard against the same station having different names.
    minimum_interstation_distance_in_m=100.0)

# Restrict the number of providers if you know which serve the desired
# data. If in doubt just don't specify - then all providers will be
# queried.

Netinv = client.get_stations(
        network = restrictions.network,
        station = restrictions.station,
        channel = restrictions.channel,
        starttime = restrictions.starttime,
        endtime = restrictions.endtime,
        maxlatitude = domain.maxlatitude,
        minlatitude = domain.minlatitude,
        maxlongitude = domain.maxlongitude,
        minlongitude = domain.minlongitude
    )
Netinv.write('data/station.txt', format="STATIONTXT", level='station')

mdl = MassDownloader(providers=["IRIS"])
mdl.download(domain, restrictions, mseed_storage="data/waveform/{network}.{station}/{network}.{station}.{location}.{channel}__{starttime}__{endtime}.mseed",
             stationxml_storage="data/stations")