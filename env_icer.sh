# check python environment first
# clean all environment
module purge
deactivate
conda deactivate

# load python module
module load GCCcore/12.3.0
module load Python/3.11.3

# create virtual env
python3 -m venv ~/phasenet-tf
source ~/phasenet-tf/bin/activate
conda create -n pntf python=3.11.3
conda activate pntf

# Install mseed
git clone https://github.com/EarthScope/mseedindex.git
cd mseedindex
make
cd ..

# Install PhaseNet-TF
git clone https://github.com:Aaaapril4/PhaseNet-TF.git
conda install conda-forge::poetry
cd PhaseNet-TF
rm *lock
poetry install --with train