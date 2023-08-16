# Meta-cognitive machines
#
# 2D matrix (world for our MCMs)
#
# Authors: {svc, lucy}@dmi.uns.ac.rs

import random
import re

# Moore neighborhood: offsets
dx = [-1, -1, -1, 0, 0, 1, 1, 1]
dy = [-1, 0, 1, -1, 1, -1, 0, 1]
        

# Moore neighborhood: link types in pattern graphs 
link_type = ["UL", "U", "UR", "L", "R", "DL", "D", "DR"]


"""
Function creates an empty matrix of dimensions <dimx, dimy>
"""
def create_empty_matrix(dimx, dimy):
    mat = []
    for _ in range(dimx):
        row = [' '] * dimy
        mat.append(row)

    return mat


"""
Function creates a random matrix of dimensions <dimx, dimy> 
populated with symbol with probability p
"""
def create_random_matrix(dimx, dimy, p, symbol):
    mat = create_empty_matrix(dimx, dimy)
    for i in range(dimx):
        for j in range(dimy):
            r = random.random()
            if r <= p:
                mat[i][j] = symbol

    return mat


"""
function loads pattern matrix from provided file
it returns the name of the concept or the scene (first line in the file)
and the matrix of symbols loaded from file (all other lines)
"""
def load_matrix(file):
    with open(file) as f:
        lines = [line.rstrip() for line in f]

    conceptName = lines[0]
    dimx = len(lines) - 1
    dimy = 0
    for i in range(1, len(lines)):
        l = len(lines[i])
        if l > dimy:
            dimy = l

    mat = create_empty_matrix(dimx, dimy)
    
    for i in range(1, len(lines)):
        l = lines[i]
        for j in range(len(l)):
            c = l[j]
            if c != ' ':
                mat[i - 1][j] = c

    return conceptName, mat


"""
simple function to print matrix
"""
def print_matrix(mat):
    for i in range(len(mat)):
        print("".join(mat[i]))


"""
function that parses string representation of field coordinates
"""
def parse_field(f):
    l = re.split("-", f)
    return int(l[0]), int(l[1])


"""
function that checks whether two fields are neighbours
"""

def neigh(f1, f2):
    f1_x, f1_y = parse_field(f1)
    f2_x, f2_y = parse_field(f2)
    return _neigh(f1_x, f1_y, f2_x, f2_y)


def _neigh(f1_x, f1_y, f2_x, f2_y):
    if f1_x == f2_x and f1_y == f2_y:
        return True, "ID"

    _dx = f1_x - f2_x
    _dy = f1_y - f2_y

    if abs(_dx) <= 1 and abs(_dy) <= 1:
        lt = ""
        for i in range(len(link_type)):
            if _dx == dx[i] and _dy == dy[i]:
                lt = link_type[i]
                break

        if lt == "":
            print("[Warning, Matrix.py] Strange neighbours: ", _dx, _dy)
            return False, None
    
        return True, lt
    else:
        return False, None
    
    
"""
function to determine the first nonempty field in a matrix
"""
def determine_first_nonempty_pixel(mat):
    dimx, dimy = len(mat), len(mat[0])
    for i in range(dimx):
        for j in range(dimy):
            if mat[i][j] != ' ':
                return i, j
    


"""
check whether fields set covers 
"""
def coverage(fields, mat):
    dimx, dimy = len(mat), len(mat[0])
    for i in range(dimx):
        for j in range(dimy): 
            f = mat[i][j]
            f_str = str(i) + "-" + str(j)
            if f != ' ' and f_str not in fields:
                return False
                
    return True