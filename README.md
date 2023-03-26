# ogr_tiller
Serve vector tiles from local spatial data


# Installation

Installation
```
conda create -n ogr_tiller -y
conda activate ogr_tiller
conda config --env --add channels conda-forge
conda config --env --set channel_priority strict
conda install python=3 fiona -y

pip3 install ogr_tiller
```

for updating to latest release
```console
pip install ogr_tiller -U
```

# Usage

```
ogr_tiller --cache_folder ./cache/ --data_folder ./data/
```

```
ogr_tiller --cache_folder ./cache/ --data_folder ./data/ --port 8000
```