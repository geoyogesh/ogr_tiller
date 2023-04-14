from ogr_tiller.poco.job_param import JobParam
from ogr_tiller.poco.tileset_manifest import TilesetManifest
from ogr_tiller.utils.fast_api_utils import set_tile_timeout
from ogr_tiller.utils.ogr_utils import get_tile_json, get_tileset_manifest, setup_ogr_cache, setup_stylesheet_cache
from ogr_tiller.utils.sqlite_utils import setup_mbtile_cache



def common(job_param: JobParam):
    tilesets = setup_ogr_cache(job_param.data_folder)

    # setup mbtile cache
    if not job_param.disable_caching:
        for tileset in tilesets:
            manifest: TilesetManifest = get_tileset_manifest()[tileset]
            tilejson = get_tile_json(tileset, job_param.port, manifest)
            setup_mbtile_cache(tileset, job_param.cache_folder, tilejson)
    

    # set tile timeout 
    set_tile_timeout(job_param.tile_timeout)

    # user stylesheets
    setup_stylesheet_cache(job_param.stylesheet_folder)
