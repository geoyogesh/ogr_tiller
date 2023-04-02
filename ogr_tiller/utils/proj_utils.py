from pyproj import Transformer

def get_bbox_for_crs(from_crs, to_crs, bbox):
    transformer = Transformer.from_crs(from_crs, to_crs, always_xy=True)
    xmin, ymin = transformer.transform(bbox[0], bbox[1])
    xmax, ymax = transformer.transform(bbox[2], bbox[3])
    return (xmin, ymin, xmax, ymax)