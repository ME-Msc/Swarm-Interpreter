"""Simple Travelling Salesperson Problem (TSP) on a circuit board."""

import math
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

class TspSolver():
	def __init__(self, locations, vehicles_num):
		self.map_locations = locations
		self.data = {}
		self.data["distance_matrix"] = self.compute_euclidean_distance_matrix()
		self.data["vehicles_num"] = vehicles_num
		self.data["depot"] = 0	# depot: The index of the depot. The location where all vehicles start and end.
		self.routes = self.generate_routes()
		self.routes_locations = self.generate_routes_locations()


	def get_closest_point_index(self, map_or_route, pos_x, pos_y):
		distances = [abs(point[0] - pos_x) + abs(point[1] - pos_y) for point in map_or_route]
		closest_point_index = min(range(len(map_or_route)), key=lambda x: distances[x])
		return closest_point_index

	
	def compute_euclidean_distance_matrix(self):
		"""Creates callback to return distance between points."""
		distances = {}
		for from_counter, from_node in enumerate(self.map_locations):
			distances[from_counter] = {}
			for to_counter, to_node in enumerate(self.map_locations):
				if from_counter == to_counter:
					distances[from_counter][to_counter] = 0
				else:
					# Euclidean distance
					distances[from_counter][to_counter] = int(
						math.hypot((from_node[0] - to_node[0]), (from_node[1] - to_node[1]))
					)
		return distances
	

	def generate_routes(self):
		# Create the routing index manager.
		manager = pywrapcp.RoutingIndexManager(
			len(self.data["distance_matrix"]), self.data["vehicles_num"], self.data["depot"]
		)

		# Create Routing Model.
		routing = pywrapcp.RoutingModel(manager)

		# Create and register a transit callback.
		def distance_callback(from_index, to_index):
			"""Returns the distance between the two nodes."""
			# Convert from routing variable Index to distance matrix NodeIndex.
			from_node = manager.IndexToNode(from_index)
			to_node = manager.IndexToNode(to_index)
			return self.data["distance_matrix"][from_node][to_node]

		transit_callback_index = routing.RegisterTransitCallback(distance_callback)

		# Define cost of each arc.
		routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

		# Add Distance constraint.
		dimension_name = "Distance"
		routing.AddDimension(
			transit_callback_index,
			0,  # no slack
			2000,  # vehicle maximum travel distance
			True,  # start cumul to zero
			dimension_name,
		)
		distance_dimension = routing.GetDimensionOrDie(dimension_name)
		distance_dimension.SetGlobalSpanCostCoefficient(100)

		# Setting first solution heuristic.
		search_parameters = pywrapcp.DefaultRoutingSearchParameters()
		search_parameters.first_solution_strategy = (
			routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
		)

		# Solve the problem.
		solution = routing.SolveWithParameters(search_parameters)

		"""Get vehicle routes from a solution and store them in an array."""
		# Get vehicle routes and store them in a two dimensional array whose
		# i,j entry is the jth location visited by vehicle i along its route.
		routes = []
		for route_nbr in range(routing.vehicles()):
			index = routing.Start(route_nbr)
			route = [manager.IndexToNode(index)]
			while not routing.IsEnd(index):
				index = solution.Value(routing.NextVar(index))
				route.append(manager.IndexToNode(index))
			routes.append(route)
		return routes


	def generate_routes_locations(self):
		routes_locations = []
		for i, route in enumerate(self.routes):
			locations = []
			for point_index in route:
				locations.append(self.map_locations[point_index])
			print('Route', i , "Locations", locations)
			routes_locations.append(locations)
		return routes_locations
	

def coverTspSolver(geojson_map):
	locations = [point.coords[0] for point in geojson_map.geometry]
	solver = TspSolver(locations, 3)
	return solver.routes_locations

if __name__ == "__main__":
	import Map
	geojson_map = Map.load_geojson("AirsimNH.geojson")
	locations = [point.coords[0] for point in geojson_map.geometry]
	simple_map = geojson_map
