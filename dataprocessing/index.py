# %%
from obspy.clients.filesystem.tsindex import Indexer
from mpi4py import MPI
import numpy as np
import os

comm = MPI.COMM_WORLD  # pylint: disable=c-extension-no-member
size = comm.Get_size()
rank = comm.Get_rank()

# %%
def get_process_list_this_rank(start_num: int, end_num: int):
    '''
    assign directories to different rank
    '''
    process_list = list(range(start_num, end_num))
    process_list_this_rank = np.array_split(process_list, size)[rank]

    return process_list_this_rank

# %%
def per_index(datadir: str, dataname: str):
    '''
    @datadir: the data directory you want to index
    @dataname: the name for you data file
    '''
    indexer = Indexer(datadir, filename_pattern='*.mseed',database=dataname,
                    index_cmd="/mnt/home/jieyaqi/code/mseedindex/mseedindex", parallel=1)
    indexer.run()
    return

# %%
def index_rank(process_list_this_rank: list):
    '''
    index directory on different ranks
    '''
    for num in process_list_this_rank:
        per_index(num, f'./data{num}', f'data{num}.sqlite')
    return

if __name__ == "__main__":
    # use mpi for multiple directory
    # process_list_this_rank = get_process_list_this_rank(38, 117)
    # index_rank()
    if not os.path.exists('./data'):
        os.mkdir('./data')

    # run for one case, usage: per_index(directory, outputfile)
    per_index('./data/waveform', 'data/data.sqlite')