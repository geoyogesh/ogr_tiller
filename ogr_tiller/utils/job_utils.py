from ogr_tiller.poco.job_param import JobParam
from ogr_tiller.utils.ogr_utils import setup_ogr_cache
from ogr_tiller.utils.sqlite_utils import setup_mbtile_cache


def common(job_param: JobParam):
    # setup mbtile cache
    if not job_param.disable_caching:
        setup_mbtile_cache(job_param.cache_folder)
    setup_ogr_cache(job_param.data_folder)