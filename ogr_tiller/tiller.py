from fastapi import FastAPI
from ogr_tiller.cache_builder import build_cache
from ogr_tiller.poco.tileset_manifest import TilesetManifest
from ogr_tiller.utils.job_utils import common
from ogr_tiller.utils.ogr_utils import get_stylesheets, get_tile_json, get_tileset_manifest, get_tilesets
from ogr_tiller.poco.job_param import JobParam
import uvicorn
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response
from ogr_tiller.utils.fast_api_utils import TimeOutException, timeout_response

from ogr_tiller.utils.sqlite_utils import read_cache, setup_mbtile_cache, update_cache
from ogr_tiller.utils.stylesheet_utils import get_starter_style
import ogr_tiller.utils.tile_utils as tile_utils
import json
from fastapi.responses import FileResponse

from fastapi.middleware.gzip import GZipMiddleware
from rich import print
import os


def start_api(job_param: JobParam):
    # setup mbtile cache
    common(job_param)

    app = FastAPI()
    app.add_middleware(GZipMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/styles/user/")
    async def get_user_style_list():
        headers = {
            "content-type": "application/json",
            "Cache-Control": 'no-cache, no-store'
        }
        stylesheets = get_stylesheets()
        return Response(content=json.dumps(stylesheets), headers=headers)

    @app.get("/styles/user/{stylesheet}.json", response_class=FileResponse)
    async def get_style_json(stylesheet: str):
        headers = {
            "content-type": "application/json",
            "Cache-Control": 'no-cache, no-store'
        }
        return FileResponse(os.path.join(job_param.stylesheet_folder, f'{stylesheet}.json'), headers=headers)

    @app.get("/styles/system/starter.json")
    async def get_style_json():
        tilesets = get_tilesets()
        data = get_starter_style(
            job_param.port, tilesets, job_param.data_folder)
        headers = {
            "content-type": "application/json",
            "Cache-Control": 'no-cache, no-store'
        }
        return Response(content=json.dumps(data), headers=headers)

    @app.get("/tilesets/{tileset}/info/tile.json")
    async def get_tileset_info(tileset: str):
        headers = {
            "content-type": "application/json",
            "Cache-Control": 'no-cache, no-store'
        }
        if tileset not in get_tilesets():
            return Response(status_code=404, headers=headers)

        data = get_tile_json(tileset, job_param.port,
                             get_tileset_manifest()[tileset])

        return Response(content=json.dumps(data), headers=headers)

    @app.get("/tilesets/{tileset}/tiles/{z}/{x}/{y}.mvt")
    async def get_tile(tileset: str, z: int, x: int, y: int):
        headers = {
            "content-type": "application/vnd.mapbox-vector-tile",
            "Cache-Control": 'no-cache, no-store'
        }

        if tileset not in get_tilesets():
            return Response(status_code=404, headers=headers)

        manifest: TilesetManifest = get_tileset_manifest()[tileset]

        if job_param.mode == 'serve_cache' or not job_param.disable_caching:
            cached_data = read_cache(tileset, x, y, z)
            if cached_data is not None:
                return Response(content=cached_data, headers=headers)

        # tile not found return 404 directly
        if job_param.mode == 'serve_cache':
            return Response(status_code=404, headers=headers)

        data = None
        try:
            data = tile_utils.get_tile(tileset, x, y, z, manifest.extent)
            if data is None:
                return Response(status_code=404, headers=headers)

        except TimeOutException:
            return timeout_response()

        # update cache
        if not job_param.disable_caching:
            update_cache(tileset, x, y, z, data)
        return Response(content=data, headers=headers)

    @app.get("/")
    async def index():
        stylesheets = get_stylesheets()
        tile_urls = [
            f'http://0.0.0.0:{job_param.port}/tilesets/{tileset}/info/tile.json'
            for tileset in get_tilesets()
        ]
        result = {
            "styles": {
                "system": {
                    "starter": f'http://0.0.0.0:{job_param.port}/styles/system/starter.json'
                },
                "user": {stylesheet: f'http://0.0.0.0:{job_param.port}/styles/user/{stylesheet}.json'  for stylesheet in stylesheets}
            },
            "tilesets": tile_urls
        }

        return result

    uvicorn.run(app, host="0.0.0.0", port=int(job_param.port))


def start_tiller_process(job_param: JobParam):
    print('started...')
    print('mode:', job_param.mode)
    print('data_folder:', job_param.data_folder)
    print('cache_folder:', job_param.cache_folder)
    print('port:', job_param.port)
    print('tile_timeout:', job_param.tile_timeout)

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
    job_param = JobParam('serve', data_folder, cache_folder,
                         None, port, disable_caching, '3')
    start_tiller_process(job_param)
