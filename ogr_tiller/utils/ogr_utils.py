from typing import Any
import fiona
from shapely.geometry import box, shape
import os
from ogr_tiller.poco.tileset_manifest import TilesetManifest
from ogr_tiller.utils.fast_api_utils import abort_after
from ogr_tiller.utils.proj_utils import get_bbox_for_crs
import yaml
import json
import morecantile
from rich import print

tms = morecantile.tms.get("WebMercatorQuad")

data_location = None
cached_tileset_names = None
cached_tileset_manifest = None
cached_user_stylesheets = []


def get_tilesets():
    return cached_tileset_names

def get_data_location():
    return data_location

def get_tileset_manifest():
    return cached_tileset_manifest

def get_stylesheets():
    return cached_user_stylesheets


def tileset_manifest(tilesets):
    result = {}
    for tileset in tilesets:
        manifest = TilesetManifest(
            name=tileset,
            minzoom=0,
            maxzoom=24,
            attribution='UNLICENSED',
            extent=4096,
            tile_buffer=64,
            simplify_tolerance=1
        )
        result[tileset] = manifest

    manifest_path = os.path.join(data_location, 'manifest.yml')
    if os.path.isfile(manifest_path):
        with open(manifest_path, 'r') as file:
            partial_manifest = json.loads(json.dumps(yaml.safe_load(file)))
            if "config" in partial_manifest and "defaults" in partial_manifest["config"]:
                defaults = partial_manifest["config"]["defaults"]
                for tileset in tilesets:
                    manifest = result[tileset]
                    if 'name' in defaults and defaults['name']:
                        manifest.name = defaults['name']
                    if 'minzoom' in defaults and defaults['minzoom']:
                        manifest.minzoom = defaults['minzoom']
                    if 'maxzoom' in defaults and defaults['maxzoom']:
                        manifest.maxzoom = defaults['maxzoom']
                    if 'attribution' in defaults and defaults['attribution']:
                        manifest.attribution = defaults['attribution']
                    if 'tile_buffer' in defaults and defaults['tile_buffer']:
                        manifest.tile_buffer = defaults['tile_buffer']
                    if 'simplify_tolerance' in defaults and defaults['simplify_tolerance']:
                        manifest.simplify_tolerance = defaults['simplify_tolerance']
                    if 'extent' in defaults and defaults['extent']:
                        manifest.extent = defaults['extent']
            if "config" in partial_manifest and "tilesets" in partial_manifest["config"] and type(partial_manifest["config"]["tilesets"]) is dict:
                current_config = partial_manifest["config"]["tilesets"].keys()
                for tileset in current_config:
                    manifest = result[tileset]
                    if 'name' in defaults and defaults['name']:
                        manifest.name = defaults['name']
                    if 'minzoom' in defaults and defaults['minzoom']:
                        manifest.minzoom = defaults['minzoom']
                    if 'maxzoom' in defaults and defaults['maxzoom']:
                        manifest.maxzoom = defaults['maxzoom']
                    if 'attribution' in defaults and defaults['attribution']:
                        manifest.attribution = defaults['attribution']

    return result


def setup_ogr_cache(data_folder):
    # update global variablea
    global data_location, cached_tileset_names, cached_tileset_manifest
    data_location = data_folder
    cached_tileset_names = []
    dir_list = os.listdir(data_location)
    for file in dir_list:
        if file.endswith('.gpkg'):
            cached_tileset_names.append(file.split('.')[0])
    cached_tileset_manifest = tileset_manifest(cached_tileset_names)


def setup_stylesheet_cache(stylesheet_folder):
    global cached_user_stylesheets
    if stylesheet_folder:
        stylesheets = [file.split('.')[0] for file in os.listdir(stylesheet_folder) if file.endswith('.json')]
        cached_user_stylesheets = stylesheets



def format_layer_name(name: str):
    return name.lower()


def format_field_name(name: str):
    return name.lower()


def format_field_type(name: str):
    return name.lower()


def get_tile_json(tileset: str, port: str, tileset_manifest: TilesetManifest) -> Any:
    result = {
        'tilejson': '3.0.0',
        'id': tileset_manifest.name,
        'name': tileset_manifest.name,
        'description': tileset_manifest.name,
        'version': '1.0.0',
        'attribution': tileset_manifest.attribution,
        'scheme': 'xyz',
        'tiles': [f'http://localhost:{port}/tilesets/' + tileset + '/tiles/{z}/{x}/{y}.mvt'],
        'minzoom': tileset_manifest.minzoom,
        'maxzoom': tileset_manifest.maxzoom,
        'bounds': None,
        'center': None
    }
    ds_path = os.path.join(data_location, f'{tileset}.gpkg')
    layers = fiona.listlayers(ds_path)

    vector_layers = []
    for layer_name in layers:
        fields = {}
        geometry_type = None
        with fiona.open(ds_path, 'r', layer=layer_name) as layer:
            result['crs'] = str(layer.crs)
            result['crs_wkt'] = layer.crs_wkt
            schema = layer.schema
            geometry_type = layer.schema['geometry']
            for field_name, field_type in schema['properties'].items():
                fields[format_field_name(field_name)
                       ] = format_field_type(field_type)

            # layer bounds cannot be computed if layer dont have any features
            try:
                minx, miny, maxx, maxy = layer.bounds
                if result['bounds'] is None:
                    result['bounds'] = [minx, miny, maxx, maxy]
                else:
                    existing_bbox = box(*result['bounds'])
                    minx_new, miny_new, maxx_new, maxy_new = existing_bbox.union(
                        box(minx, miny, maxx, maxy)).bounds
                    result['bounds'] = [minx_new, miny_new, maxx_new, maxy_new]
            except:
                print(f'error getting bounds for {layer_name}')
        vector_layers.append({
            'id': layer_name,
            'fields': fields,
            'geometryType': geometry_type
        })

        # include label point layer if it is polygon
        if geometry_type in ['Polygon', '3D Polygon', 'MultiPolygon', '3D MultiPolygon']:
            vector_layers.append({
                'id': f'{layer_name}_label',
                'fields': fields,
                'geometryType': 'Point'
            })

    result['vector_layers'] = vector_layers

    # reproject bounds
    if result['crs'] != 'EPSG:4326' and result['bounds'] is not None:
        bounds = get_bbox_for_crs(result['crs'], 'EPSG:4326', result['bounds'])
        result['bounds'] = bounds
        result['center'] = [(bounds[0] + bounds[2]) / 2,
                            (bounds[1] + bounds[3]) / 2]
    else:
        result['center'] = None

    return result










