from fastapi import FastAPI
from ogr_tiller.utils.ogr_utils import get_features_no_abort, get_starter_style, get_tile_json, get_features, get_tileset_manifest, get_tilesets
from ogr_tiller.poco.job_param import JobParam
import uvicorn
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response
from ogr_tiller.utils.ogr_utils import setup_ogr_cache
from ogr_tiller.utils.fast_api_utils import TimeOutException, timeout_response

from ogr_tiller.utils.sqlite_utils import cleanup_mbtile_cache, read_cache, setup_mbtile_cache, update_cache
import ogr_tiller.utils.tile_utils as tile_utils
import json
from supermercado import edge_finder, uniontiles, burntiles, super_utils
from shapely.geometry import box, shape, mapping
from multiprocessing.pool import ThreadPool as Pool
import multiprocessing


def common(job_param: JobParam):
    # setup mbtile cache
    if not job_param.disable_caching:
        setup_mbtile_cache(job_param.cache_folder)
    setup_ogr_cache(job_param.data_folder)

def start_api(job_param: JobParam):
    # setup mbtile cache 
    common(job_param)

    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/styles/starter.json")
    async def get_style_json():
        data = get_starter_style(job_param.port)
        headers = {
            "content-type": "application/json",
            "Cache-Control": 'no-cache, no-store'
        }
        return Response(content=json.dumps(data), headers=headers)

    @app.get("/tilesets/{tileset}/info/tile.json")
    async def get_tileset_info(tileset: str):
        if tileset not in get_tilesets():
            return Response(status_code=404)

        data = get_tile_json(tileset, job_param.port, get_tileset_manifest()[tileset])
        headers = {
            "content-type": "application/json",
            "Cache-Control": 'no-cache, no-store'
        }
        return Response(content=json.dumps(data), headers=headers)

    @app.get("/tilesets/{tileset}/tiles/{z}/{x}/{y}.mvt")
    async def get_tile(tileset: str, z: int, x: int, y: int):
        if tileset not in get_tilesets():
            return Response(status_code=404)
        
        headers = {
            "content-type": "application/vnd.mapbox-vector-tile",
            "Cache-Control": 'no-cache, no-store'
        }

        if job_param.mode == 'serve_cache' or not job_param.disable_caching:
            cached_data = read_cache(tileset, x, y, z)
            if cached_data is not None:
                return Response(content=cached_data, headers=headers)

        # tile not found return 404 directly 
        if job_param.mode == 'serve_cache':
            return Response(status_code=404, headers=headers)

        data = None
        try:
            layer_features, srid = get_features(tileset, x, y, z)
            if len(layer_features) == 0:
                return Response(status_code=404, headers=headers)
            
            
            data = tile_utils.get_tile(layer_features, x, y, z, srid)
        except TimeOutException:
            return timeout_response()

        # update cache
        if not job_param.disable_caching:
            update_cache(tileset, x, y, z, data)
        return Response(content=data, headers=headers)

    @app.get("/")
    async def index():
        tile_urls = [
            f'http://0.0.0.0:{job_param.port}/tilesets/{tileset}/info/tile.json'
            for tileset in get_tilesets()
        ]
        result = {
            "styles": {
                "starter": f'http://0.0.0.0:{job_param.port}/styles/starter.json'
            },
            "tilesets": tile_urls
        }

        return result

    uvicorn.run(app, host="0.0.0.0", port=int(job_param.port))


def build_cache(job_param: JobParam):
    # cleanup existing mbtile cache
    cleanup_mbtile_cache(job_param.cache_folder)
    # setup mbtile cache 
    common(job_param)

    tilesets = get_tilesets()
    for tileset in tilesets:
        tilejson = get_tile_json(tileset, job_param.port, get_tileset_manifest()[tileset])
        bbox = box(*tilejson['bounds'])
        fc = {
            "features": [{"type": "Feature", "geometry": a} for a in [mapping(b) for b in [bbox]]]
        }
        features = [f for f in super_utils.filter_features(fc["features"])]
        tiles = []
        for zoom in range(tilejson['minzoom'], tilejson['maxzoom'] + 1):
            tiles.extend(burntiles.burn(features, zoom))
        def process_tile(tile):
            x, y, z = tile
            x = x.item()
            y = y.item()
            z = z.item()
            try:
                layer_features, srid = get_features_no_abort(tileset, x, y, z)
                if len(layer_features) == 0:
                    return
                data = tile_utils.get_tile_no_abort(layer_features, x, y, z, srid)
                update_cache(tileset, x, y, z, data)
            except Exception:
                print(f'error generating tile for {(x, y, z)}')

        with Pool(multiprocessing.cpu_count() - 1) as p:
            p.map(process_tile, tiles)



def start_tiller_process(job_param: JobParam):
    print('started...')
    print('mode:', job_param.mode)
    print('data_folder:', job_param.data_folder)
    print('cache_folder:', job_param.cache_folder)
    print('port:', job_param.port)

    if job_param.mode == 'serve' or job_param.mode == 'serve_cache':
        print('Web UI started')
        start_api(job_param)
        print('Web UI stopped')
    elif job_param.mode == 'build_cache':
        # job to build cache
        print('started...')
        build_cache(job_param)
        print('completed...')
    print('completed')
    
    

if __name__ == "__main__":
    data_folder = './data/'
    cache_folder = './cache/'
    port = '8080'
    disable_caching = True
    job_param = JobParam('serve', data_folder, cache_folder, port, disable_caching)
    start_tiller_process(job_param)
