from fastapi import FastAPI
from ogr_tiller.entities.job_param import JobParam
import uvicorn
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response
from ogr_tiller.utils.ogr_utils import setup_ogr_cache
from ogr_tiller.utils.fast_api_utils import TimeOutException, timeout_response

import ogr_tiller.utils.ogr_utils
from ogr_tiller.utils.sqlite_utils import read_cache, setup_cache, update_cache
import ogr_tiller.utils.tile_utils as tile_utils
import json


def start_api(job_param: JobParam):
    # setup mbtile cache
    setup_cache(job_param.cache_folder)
    setup_ogr_cache(job_param.data_folder)

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
        data = ogr_tiller.utils.ogr_utils.get_starter_style(job_param.port)
        headers = {
            "content-type": "application/json",
            "Cache-Control": 'no-cache, no-store'
        }
        return Response(content=json.dumps(data), headers=headers)

    @app.get("/tilesets/{tileset}/info/tile.json")
    async def get_tileset_info(tileset: str):
        if tileset not in ogr_tiller.utils.ogr_utils.tilesets:
            return Response(status_code=404)

        data = ogr_tiller.utils.ogr_utils.get_tile_json(tileset, job_param.port)
        headers = {
            "content-type": "application/json",
            "Cache-Control": 'no-cache, no-store'
        }
        return Response(content=json.dumps(data), headers=headers)

    @app.get("/tilesets/{tileset}/tiles/{z}/{x}/{y}.mvt")
    async def get_tile(tileset: str, z: int, x: int, y: int):
        if tileset not in ogr_tiller.utils.ogr_utils.tilesets:
            return Response(status_code=404)

        cached_data = read_cache(tileset, x, y, z)
        if cached_data is not None:
            headers = {
                "content-type": "application/vnd.mapbox-vector-tile",
                "Cache-Control": 'no-cache, no-store'
            }
            return Response(content=cached_data, headers=headers)

        layer_features = ogr_tiller.utils.ogr_utils.get_features(tileset, x, y, z)
        if len(layer_features) == 0:
            return Response(status_code=404)

        data = None
        try:
            data = tile_utils.get_tile(layer_features, x, y, z)
        except TimeOutException:
            return timeout_response()

        # update cache
        update_cache(tileset, x, y, z, data)

        headers = {
            "content-type": "application/vnd.mapbox-vector-tile",
            "Cache-Control": 'no-cache, no-store'
        }
        return Response(content=data, headers=headers)

    @app.get("/")
    async def index():
        tile_urls = [
            f'http://0.0.0.0:{job_param.port}/tilesets/{tileset}/info/tile.json'
            for tileset in ogr_tiller.utils.ogr_utils.tilesets
        ]
        result = {
            "styles": {
                "starter": f'http://0.0.0.0:{job_param.port}/styles/starter.json'
            },
            "tilesets": tile_urls
        }

        return result

    uvicorn.run(app, host="0.0.0.0", port=int(job_param.port))


if __name__ == "__main__":
    data_folder = './../data/'
    cache_folder = './../cache/'
    port = '8080'
    job_param = JobParam(data_folder, cache_folder, port)
    start_api(job_param)
