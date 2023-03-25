from fastapi import FastAPI
import uvicorn
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response

from ogr_utils import get_features, get_starter_style, get_tile_json
import tile_utils
import json

def start_api():
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/tileset/info/tile.json")
    async def get_tileset_info():
        data = get_tile_json()
        headers = {
            "content-type": "application/json",
            "Cache-Control": 'no-cache, no-store'
        }
        return Response(content=json.dumps(data), headers=headers)
    
    @app.get("/styles/starter.json")
    async def get_style_json():
        data = get_starter_style()
        headers = {
            "content-type": "application/json",
            "Cache-Control": 'no-cache, no-store'
        }
        return Response(content=json.dumps(data), headers=headers)
    

    @app.get("/tileset/tiles/{z}/{x}/{y}.mvt")
    async def get_tile(z: int, x: int, y: int):
        layer_features = get_features(x, y, z)
        if len(layer_features) == 0:
            return Response(status_code=404)
        
        data = tile_utils.get_tile(layer_features, x, y, z)
        headers = {
            "content-type": "application/vnd.mapbox-vector-tile",
            "Cache-Control": 'no-cache, no-store'
        }
        return Response(content=data, headers=headers)

    @app.get("/")
    async def index():
        return "Welcome"
    
    uvicorn.run(app, host="0.0.0.0", port=8080)
    

if __name__ == "__main__":
    start_api()
