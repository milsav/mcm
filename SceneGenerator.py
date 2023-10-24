# Meta-cognitive machines
#
# Module employing discrete geometry algorithms to create scenes
# (currently supports circles, polygons, squares and rectangles) 
# 
# Authors: {svc, lucy}@dmi.uns.ac.rs

from Matrix import create_empty_matrix, print_matrix, mat_to_str

import pybresenham as geom


class SceneGenerator:
    def __init__(self, dimx=100, dimy=100, symbol='x'):
        self.dimx = dimx
        self.dimy = dimy
        self.symbol = symbol

        self.M = create_empty_matrix(dimx, dimy)


    def clear(self):
        self.M = create_empty_matrix(self.dimx, self.dimy)

    
    def print(self):
        print_matrix(self.M)


    def populate_matrix(self, points):
        for p in points:
            x, y = p[0], p[1]
            if x >= 0 and x <= self.dimx and y >= 0 and y <= self.dimy:
                self.M[x][y] = self.symbol


    def draw_circle(self, centerx, centery, radius):
        points = list(geom.circle(centerx, centery, radius))
        self.populate_matrix(points)


    def draw_polygon(self, centerx, centery, radius, sides):
        points = list(geom.polygon(centerx, centery, radius, sides))
        self.populate_matrix(points)

    
    def draw_square(self, left, top, length):
        points = list(geom.square(left, top, length))
        self.populate_matrix(points)


    def draw_rectangle(self, left, top, width, height):
        points = list(geom.rectangle(left, top, width, height))
        self.populate_matrix(points)


    def save(self, file_name, pattern=""):
        s = mat_to_str(self.M)
        if pattern == "":
            fn = file_name + ".txt"
        else:
            fn = file_name + ".pat"

        with open(fn, "w") as text_file:
            if pattern != "":
                text_file.write(pattern + "\n")
            text_file.write(s)
        





if __name__ == "__main__":
    sg = SceneGenerator(50, 50)
    sg.draw_circle(15, 15, 5)
    sg.save('test_files/circle')
    sg.draw_circle(30, 30, 8)
    sg.save('test_files/circle_scene')
    sg.print()

    """
    sg = SceneGenerator(50, 50)
    sg.draw_polygon(20, 20, 15, 6)
    sg.draw_square(1, 1, 5)
    sg.draw_rectangle(40, 40, 5, 8)
    sg.print()
    """