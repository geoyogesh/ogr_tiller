import sys
import argparse

from ogr_tiller.poco.job_param import JobParam
from ogr_tiller.tiller import start_tiller_process, start_api



def get_arg(param):
    source_index = sys.argv.index(param)
    val = sys.argv[source_index + 1]
    return val


def cli():
    parser = argparse.ArgumentParser(prog='ogr_tiller')
    parser.add_argument('--mode', help='mode', default='serve') # serve, build_cache, serve_cache
    parser.add_argument('--data_folder', help='data folder', required=True)
    parser.add_argument('--cache_folder', help='cache folder', required=True)
    parser.add_argument('--stylesheet_folder', help='stylesheet folder', default=None)
    parser.add_argument('--disable_caching', help='disable caching', default='false')
    parser.add_argument('--port', help='port', default='8080')
    parser.add_argument('--tile_timeout', help='timeout for dynamic tile generation', default='3')

    args = parser.parse_args()
    disable_caching = args.disable_caching.lower().capitalize() == 'True'
    tile_timeout = int(args.tile_timeout)
    param = JobParam(
        args.mode, 
        args.data_folder, 
        args.cache_folder, 
        args.stylesheet_folder,
        args.port, 
        disable_caching, 
        tile_timeout)
    start_tiller_process(param)
