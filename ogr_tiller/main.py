import sys
import argparse

from ogr_tiller.poco.job_param import JobParam
from ogr_tiller.tiller import start_api


def execute(job_param: JobParam):
    print('started...')
    print('data_folder:', job_param.data_folder)
    print('cache_folder:', job_param.cache_folder)
    print('port:', job_param.port)

    print('Web UI started')
    start_api(job_param)
    print('Web UI stopped')
    print('completed')


def get_arg(param):
    source_index = sys.argv.index(param)
    val = sys.argv[source_index + 1]
    return val


def cli():
    parser = argparse.ArgumentParser(prog='ogr_tiller')
    parser.add_argument('--data_folder', help='data folder', required=True)
    parser.add_argument('--cache_folder', help='cache folder', required=True)
    parser.add_argument('--disable_caching', help='disable caching', default='false')
    parser.add_argument('--port', help='port', default='8080')

    args = parser.parse_args()
    disable_caching = args.disable_caching.lower().capitalize() == 'True'
    param = JobParam(args.data_folder, args.cache_folder, args.port, disable_caching)
    execute(param)
