# Meta-cognitive machines
#
# Inference Engine module identifies concepts in a given scene
#
# Authors: {svc, lucy}@dmi.uns.ac.rs

from Matrix import load_matrix, print_matrix
from SceneAnalyzer import IdentifyObjects
from HOAutomaton import HOAPatRecKernel

def hoa_inference(scene_file, automata_memory, show_activation_history=False):
    scene_desc, scene_matrix = load_matrix(scene_file)
    print(scene_desc, " LOADED")
    print_matrix(scene_matrix)

    idobj = IdentifyObjects(scene_matrix)
    num_objects = idobj.num_objects()
    for i in range(num_objects):
        mat = idobj.get_object_matrix(i)
        print("\nStarting pattern recognition for: ")
        print_matrix(mat)

        for hoa_concept in automata_memory.get_hoa_concepts():
            hoas = automata_memory.get_automata(hoa_concept)
            try_num = 0
            for hoa in hoas:
                print("Trying", hoa_concept, try_num)
                try_num += 1
                prk = HOAPatRecKernel(hoa, mat, 0, 0)
                rec, at, visited_fields = prk.apply()
            
                if show_activation_history:
                    prk.print_activation_history()
                    
                if rec:
                    print("=================> ", hoa_concept, " recognized, activation time", at)
                    print(visited_fields)