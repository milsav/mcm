# Meta-cognitive machines
#
# Inference Engine module identifies concepts in a given scene
#
# Authors: {svc, lucy}@dmi.uns.ac.rs

from Matrix import load_matrix, print_matrix, determine_first_nonempty_pixel
from Matrix import num_pixels, parse_field, coverage
from SceneAnalyzer import IdentifyObjects
from HOAutomaton import HOAPatRecKernel
from Automaton import FSMPatRecKernel, PatternGraph 


def similarity_analysis(ac_scores):
    if ac_scores == None or len(ac_scores) == 0:
        return None
    
    sim_scores = []
    for ac in ac_scores:
        concept = ac[0]
        activation = ac[1]
        coverage = ac[2]
        sim_score = activation * coverage
        sim_scores.append((concept, sim_score))

    sim_scores.sort(key=lambda a: a[1], reverse=True)
    return sim_scores[0]


def hoa_inference(mat, automata_memory, show_activation_history):
    recognized_concepts = []
    ac_scores = []
    
    num_pixs = num_pixels(mat)

    for hoa_concept in automata_memory.get_hoa_concepts():
        hoas = automata_memory.get_automata(hoa_concept)
        for hoa in hoas:
            pos = determine_first_nonempty_pixel(mat)
            #print("Trying", hoa_concept, "at", pos)
            prk = HOAPatRecKernel(hoa, mat, pos[0], pos[1])
            rec, _, visited_fields = prk.apply()
            cov_factor = len(set(visited_fields)) / num_pixs
            ac_score = prk.activation_score()

            if show_activation_history:
                prk.print_activation_history()

            recognized = rec and coverage(visited_fields, mat)       
            if recognized:
                recognized_concepts.append(hoa_concept)
            
            if ac_score > 0:
                #print("VF: ", visited_fields, "AC = ", ac_score, "concept", hoa_concept)
                ac_scores.append((hoa_concept, ac_score, cov_factor))

    if len(ac_scores) > 0:
        print("--- HOA activation scores")
        for acs in ac_scores:
            print(acs[0], round(acs[1], 3), "coverage factor: ", round(acs[2], 3))

    print("--- HOA inference results")
    if len(recognized_concepts) > 0:
        print("Recognized concepts:", ",".join(recognized_concepts))
    else:
        print("Nothing recoginized by HOAs")
        sim_res = similarity_analysis(ac_scores)
        if sim_res != None:
            print("The most similar concept: ", sim_res[0], "similarity score", sim_res[1])


def fsm_inference(mat, automata_memory):
    pg = PatternGraph(mat)
    starts = pg.start_nodes

    if len(starts) == 0:
        return

    msgs = []

    for start in starts:
        x, y = parse_field(start)
        for concept in automata_memory.get_base_concepts():
            fsms = automata_memory.get_automata(concept)
            noauto = len(fsms)
            for k in range(noauto):
                fsm = fsms[k]
                pkr = FSMPatRecKernel(fsm, mat, x, y)
                rec, _, _ = pkr.apply()
                if rec:
                    msgs.append(concept + " recognized at (" + str(x) + ", " + str(y) + ")")
    
    if len(msgs) == 0:
        print("--- Nothing recognized by FSMs")
    else:
        print("--- FSM inference results")
        for m in msgs:
            print(m)


def inference(scene_file, automata_memory, show_activation_history=False):
    scene_desc, scene_matrix = load_matrix(scene_file)
    print(scene_desc, "loaded")

    idobj = IdentifyObjects(scene_matrix)
    num_objects = idobj.num_objects()
    for i in range(num_objects):
        mat = idobj.get_object_matrix(i)
        print("\nStarting pattern recognition for: ")
        print_matrix(mat)
        hoa_inference(mat, automata_memory, show_activation_history=show_activation_history)
        fsm_inference(mat, automata_memory)

        