import math
import numpy as np


class PointStabilized:

    def __init__(self, coordinates: tuple, history_depth: int = 5, lifespan: int = 10):
        self.coord = coordinates
        self.dimension = len(coordinates)
        self.history_coord = [coordinates]
        self.history_depth = history_depth
        self.lifespan = lifespan
        self.health = lifespan

    def check_dimensions(self, new_coordinates: tuple):

        if len(new_coordinates) != self.dimension:
            raise ValueError(f"Wrong point dimension, is {len(new_coordinates)}, should be: {self.dimension}")
        
    def is_point_approximately(self, new_coordinates: tuple, threshold: int = 50) -> bool:

        self.check_dimensions(new_coordinates)
        
        if math.dist(self.coord, new_coordinates) < threshold:
            return True
        return False
    
    def move_point(self, new_coordinates: tuple):
        
        self.check_dimensions(new_coordinates)
        
        self.coord = new_coordinates
        self.history_coord.append(new_coordinates)
        if len(self.history_coord) > self.history_depth:
            self.history_coord.pop(0)
        self.coord = np.average(self.history_coord, axis=0)

    def pick_point_from_list(self, list_with_points: list, threshold: int = 50) -> list:

        for point in list_with_points:
            if self.is_point_approximately(point, threshold=threshold):
                self.move_point(point)
                self.health = self.lifespan # restore health
                return list_with_points.remove(point)
            
        # age the point if not found
        if self.health:
            self.health -= 1
        return list_with_points
    

def handle_stabilized_points(blob_objects_list: list, found_coord_list: list) -> tuple[list, list]:

    # stabilization of objects coordinates
    for blob in blob_objects_list:
        blob.pick_point_from_list(found_coord_list, 100)
    # remove dead points
    blob_objects_list = list(filter(lambda x: x.health, blob_objects_list))
    # creation of new blob objects
    if len(found_coord_list):
        for new_object in found_coord_list:
            blob_objects_list.append(PointStabilized(new_object))

    # prepare new list of objects coordinates
    # filter added to not show very new objects
    stabilized_found_coord_list = [blob.coord for blob in filter(lambda x: len(x.history_coord) > 3, blob_objects_list)]

    return blob_objects_list, stabilized_found_coord_list

        




        