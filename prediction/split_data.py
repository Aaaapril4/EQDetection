from pathlib import Path
from generate_csv import generate_csv
from generate_yaml import generate_yaml
root = Path('/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_v1')
datadir = root / "data"

filelist = list(datadir.glob("*.mseed"))
nperdir = 155
ndir = len(filelist) // nperdir + bool(len(filelist) % nperdir)
dirmap = {}
start = 1

# create data directories and output directories
numdir = 0
while numdir < ndir:
    num = numdir + start
    datap = root / f'data{num}'
    resultp = root / f'result{num}'
    datap.mkdir(parents=True, exist_ok=True)
    resultp.mkdir(parents=True, exist_ok=True)
    dirmap[numdir] = datap
    numdir += 1

# split all files into each folder 
for idx, file in enumerate(filelist):
    p = dirmap[idx % ndir]
    file.rename(p / file.name)

# generate csv and yaml file
for i in dirmap.keys():
    num = i + start
    generate_csv(root / f'data{num}',  root / f'statime{num}.csv')
    generate_yaml(i + start)
