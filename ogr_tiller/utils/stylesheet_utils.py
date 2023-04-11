import random
from typing import Any, List
import fiona
import os

def get_starter_style(port: str, cached_tileset_names: List[str], data_location: str) -> Any:
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

    layer_geometry_types = []
    for tileset in cached_tileset_names:
        ds_path = os.path.join(data_location, f'{tileset}.gpkg')
        layers = fiona.listlayers(ds_path)
        for layer_name in layers:
            with fiona.open(ds_path, 'r', layer=layer_name) as layer:
                layer_geometry_types.append(
                    (tileset, layer_name, layer.schema['geometry']))

    geometry_order = [
        'Point',
        '3D Point',
        'MultiPoint',
        '3D MultiPoint',
        'LineString',
        '3D LineString',
        'MultiLineString',
        '3D MultiLineString',
        'Polygon',
        '3D Polygon',
        'MultiPolygon',
        '3D MultiPolygon',
        'Unknown',
        'GeometryCollection',
        '3D GeometryCollection']
    layer_index = 0
    for orderGeometry in geometry_order:
        for tileset, layer_name, geometryType in layer_geometry_types:
            if orderGeometry == geometryType:
                # getting color for layer
                color = get_color(layer_index)
                layer_index += 1

                if geometryType in [
                    'Unknown',
                    'GeometryCollection',
                    '3D GeometryCollection'
                ]:
                    for g in ['Point', 'LineString', 'Polygon']:
                        style_json['layers'].append(get_layer_style(
                            tileset, color, f'{layer_name}_{g.lower()}', layer_name, g))
                else:
                    style_json['layers'].append(get_layer_style(
                        tileset, color, layer_name, layer_name, orderGeometry))

    return style_json

def get_color(i: int):
    colors = ['#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99', '#e31a1c',
              '#fdbf6f', '#ff7f00', '#cab2d6', '#6a3d9a', '#ffff99', '#b15928']
    if i < len(colors):
        return colors[i]
    return f"#{''.join([random.choice('0123456789ABCDEF') for i in range(6)])}"

def get_layer_style(tileset: str, color: str, layer_name: str, source_layer: str, geometry_type: str) -> Any:
    if geometry_type in ['LineString', '3D LineString', 'MultiLineString', '3D MultiLineString']:
        return {
            'id': layer_name,
            'type': 'line',
            'source': tileset,
            'source-layer': source_layer,
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
    elif geometry_type in ['Polygon', '3D Polygon', 'MultiPolygon', '3D MultiPolygon']:
        return {
            'id': layer_name,
            'type': 'line',
            'source': tileset,
            'source-layer': source_layer,
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
    elif geometry_type in ['Point', '3D Point', 'MultiPoint', '3D MultiPoint']:
        return {
            'id': layer_name,
            'type': 'circle',
            'source': tileset,
            'source-layer': source_layer,
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
