
```
conda create -n ogr_tiller
conda activate ogr_tiller
conda config --env --add channels conda-forge
conda config --env --set channel_priority strict
conda install python=3 fiona mapbox-vector-tile rtree mapbox-vector-tile[proj] pyproj -y
conda install -y fastapi uvicorn 

pip install morecantile
```


http://0.0.0.0:8080/tilesets/detailed_streetview/info/tile.json
http://0.0.0.0:8080/tilesets/detailed_streetview/tiles/0/0/0.mvt
http://0.0.0.0:8080/styles/starter.json
