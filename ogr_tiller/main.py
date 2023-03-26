import sys
import os
import argparse

from ogr_tiller.entities.job_param import JobParam
from ogr_tiller.ogr_tiller import start_api


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
    parser.add_argument('--port', help='port', default='8080')

    args = parser.parse_args()
    param = JobParam(args.data, args.cache, args.port)
    execute(param)
