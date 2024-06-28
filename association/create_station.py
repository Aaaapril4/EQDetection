import pandas as pd

station = pd.read_csv('data/station.txt', delimiter='|')
station['id'] = station.apply(lambda x: f'{x["#Network"]}.{x["Station"]}..BH'.replace(' ', ''), axis = 1)
station = station[["id", "Longitude", "Latitude", "Elevation", "Station"]]
station.columns = ["id", "longitude", "latitude", "elevation(m)", "station"]
station.to_csv('data/stations.csv', 
               index = False)