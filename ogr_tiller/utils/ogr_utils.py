from typing import Any
import fiona
import mercantile
from shapely.geometry import box
from shapely.geometry import shape
import random
import os
from shapely.ops import clip_by_rect

data_location = None
cached_tileset_names = None


def get_tilesets():
    return cached_tileset_names


def setup_ogr_cache(data_folder):
    # update global variablea
    global data_location, cached_tileset_names
    data_location = data_folder
    cached_tileset_names = []
    dir_list = os.listdir(data_location)
    for file in dir_list:
        if file.endswith('.gpkg'):
            cached_tileset_names.append(file.split('.')[0])


def format_layer_name(name: str):
    return name.lower()


def format_field_name(name: str):
    return name.lower()


def format_field_type(name: str):
    return name.lower()


def get_tile_json(tileset: str, port: str) -> Any:
    result = {
        'tilejson': '3.0.0',
        'id': 'ogr_tiller_tileset',
        'name': 'ogr_tiller_tileset',
        'description': 'OGR Tiller Tileset',
        'version': '1.0.0',
        'attribution': 'UNLICENSED',
        'scheme': 'xyz',
        'tiles': [f'http://localhost:{port}/tilesets/' + tileset + '/tiles/{z}/{x}/{y}.mvt'],
        'minzoom': 0,
        'maxzoom': 22,
        'bounds': None,
        'center': None
    }
    ds_path = os.path.join(data_location, f'{tileset}.gpkg')
    layers = fiona.listlayers(ds_path)

    vector_layers = []
    for layer_name in layers:
        fields = {}
        with fiona.open(ds_path, 'r', layer=layer_name) as layer:
            result['crs'] = str(layer.crs)
            result['crs_wkt'] = layer.crs_wkt
            schema = layer.schema
            for field_name, field_type in schema['properties'].items():
                fields[format_field_name(field_name)] = format_field_type(field_type)
            
            minx, miny, maxx, maxy = layer.bounds
            if result['bounds'] is None:
                result['bounds'] = [minx, miny, maxx, maxy]
            else:
                existing_bbox = box(result['bounds'][0],result['bounds'][1],result['bounds'][2],result['bounds'][3])
                minx_new, miny_new, maxx_new, maxy_new = existing_bbox.union(box(minx, miny, maxx, maxy)).bounds
                result['bounds'] = [minx_new, miny_new, maxx_new, maxy_new]

        vector_layers.append({
            'id': layer_name,
            'fields': fields
        })
    
    result['vector_layers'] = vector_layers
    result['center'] = None if result['bounds'] is None else [(result['bounds'][0] + result['bounds'][2]) / 2, (result['bounds'][1] + result['bounds'][3]) / 2]
    return result


def get_starter_style(port: str) -> Any:
    style_json = {
        'version': 8,
        'sources': {},
        'layers': [],
    }

    for tileset in cached_tileset_names:
        style_json['sources'][tileset] = {
                'type': 'vector',
                'url': f'http://0.0.0.0:{port}/tilesets/{tileset}/info/tile.json'
            }

    for tileset in cached_tileset_names:
        ds_path = os.path.join(data_location, f'{tileset}.gpkg')
        layer_geometry_types = []
        layers = fiona.listlayers(ds_path)
        for layer_name in layers:
            with fiona.open(ds_path, 'r', layer=layer_name) as layer:
                layer_geometry_types.append((tileset, layer_name, layer.schema['geometry']))

    geometry_order = ['Point', 'MultiPoint', 'LineString', 'MultiLineString', 'Polygon', 'MultiPolygon']
    layer_index = 0
    for orderGeometry in geometry_order:
        color = get_color(layer_index)
        for tileset, layer_name, geometryType in layer_geometry_types:
            if orderGeometry == geometryType:
                style_json['layers'].append(get_layer_style(tileset, color, layer_name, orderGeometry))
        layer_index += 1
    
    return style_json


def get_layer_style(tileset: str, color: str, layer_name: str, geometry_type: str) -> Any:
    if geometry_type == 'LineString' or geometry_type == 'MultiLineString':
        return {
            'id': layer_name,
            'type': 'line',
            'source': tileset,
            'source-layer': layer_name,
            'filter': ["==", "$type", "LineString"],
            'layout': {
                'line-join': 'round',
                'line-cap': 'round'
            },
            'paint': {
                'line-color': color,
                'line-width': 1,
                'line-opacity': 0.75
            }
        }
    elif geometry_type == 'Polygon' or geometry_type == 'MultiPolygon':
        return {
            'id': layer_name,
            'type': 'line',
            'source': tileset,
            'source-layer': layer_name,
            'filter': ["==", "$type", "Polygon"],
            'layout': {
                'line-join': 'round',
                'line-cap': 'round'
            },
            'paint': {
                'line-color': color,
                'line-width': 1,
                'line-opacity': 0.75
            }
        }
    elif geometry_type == 'Point' or geometry_type == 'MultiPoint':
        return {
            'id': layer_name,
            'type': 'circle',
            'source': tileset,
            'source-layer': layer_name,
            'filter': ["==", "$type", "Point"],
            'paint': {
                'circle-color': color,
                'circle-radius': 2.5,
                'circle-opacity': 0.75
            }
        }
    else:
        print('unhandled geometry type')
    return None


def get_color(i: int):
    colors = ['#a6cee3','#1f78b4','#b2df8a','#33a02c','#fb9a99','#e31a1c','#fdbf6f','#ff7f00','#cab2d6','#6a3d9a','#ffff99','#b15928'];
    if i < len(colors):
        return colors[i]
    return f"#{''.join([random.choice('0123456789ABCDEF') for i in range(6)])}"


def get_features(tileset: str, x: int, y: int, z: int):
    bbox_bounds = mercantile.bounds(x, y, z)
    bbox = (bbox_bounds.west, bbox_bounds.south, bbox_bounds.east, bbox_bounds.north)

    ds_path = os.path.join(data_location, f'{tileset}.gpkg')
    layers = fiona.listlayers(ds_path)
    result = []

    for layer_name in layers:
        processed_features = []
        with fiona.open(ds_path, 'r', layer=layer_name) as layer:
            features = layer.filter(bbox=bbox)
            for feat in features:
                processed_features.append({
                    "geometry": clip_by_rect(
                        shape(feat.geometry),
                        bbox[0],
                        bbox[1],
                        bbox[2],
                        bbox[3],
                    ),
                    "properties": feat.properties
                })
        result.append((layer_name, processed_features))
    return result
    