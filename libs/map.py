import json
import os
import geopandas as gpd

def load_geojson(filename):
	current_dir = os.path.dirname(os.path.abspath(__file__))
	file_path = os.path.join(current_dir, 'data\\', filename)
	gdf = gpd.read_file(file_path)
	# print(gdf)
	return gdf

def generate_grip_geojson(filename, x_start, x_end, x_step, y_start, y_end, y_step):
	features = []

	x = x_start
	while x <= x_end:
		y = y_start
		while y <= y_end:
			point = {
				"type": "Feature",
				"properties": {},
				"geometry": {
					"type": "Point",
					"coordinates": [x, y]
				}
			}
			features.append(point)
			y += y_step
		x += x_step

	geojson = {
		"type": "FeatureCollection",
		"features": features
	}
	
	# 保存到文件
	output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/', filename)
	with open(output_file, 'w') as f:
		json.dump(geojson, f)

AirsimNH = load_geojson("AirsimNH.geojson")

testMap = load_geojson("testMap.geojson")
	
if __name__ == "__main__":
	fn = "testMap.geojson"
	generate_grip_geojson(fn, 0, 40, 20, 0, 40, 20)
	data = load_geojson(fn)