# Meta-cognitive machines
#
# HOAutomaton module constains functions and classes 
# for pattern recognition based on higher-order automata
# combining base automata 
#
# As base automata, HO automata are also constructed from 
# 2D matrix patterns
#
# Authors: {svc, lucy}@dmi.uns.ac.rs


from AutomataMemory import base_automata_memory
from Automaton import FSMPatRecKernel
from Matrix import neigh, parse_field

class HOALearner:
    def __init__(self, matrix, verbose=False):
        self.matrix = matrix
        self.dim_x = len(matrix)
        self.dim_y = len(matrix[0])
        self.verbose = verbose

    #
    # identify base automata that can be activated in pattern matrix
    # 
    def identify_base_automata(self):
        # set of visited matrix fields
        visited_fields = set()

        # list of activated base automata
        self.activated_automata = []

        base_concepts = base_automata_memory.get_concepts()

        for i in range(self.dim_x):
            for j in range(self.dim_y):
                start_field = str(i) + "-" + str(j)
                if self.matrix[i][j] != ' ' and start_field not in visited_fields:
                    for concept in base_concepts:
                        for automata in base_automata_memory.get_automata(concept): 
                            prk = FSMPatRecKernel(automata, self.matrix, i, j)
                            rec, t, visited = prk.apply()
                            if rec:
                                # check valid activations
                                valid_activation = False
                                for v in visited:
                                    if v != start_field and not v in visited_fields:
                                        valid_activation = True
                                        break

                                if valid_activation:
                                    for v in visited:
                                        visited_fields.add(v)

                                    self.activated_automata.append([concept, automata, visited, t])      

        if self.verbose:
            print("Activated base automata")
            for a in self.activated_automata:
                print(a[0])
                a[1].print()
                print(a[2])
                print(a[3])
                print("\n")

    
    def infere_automata_dependencies(self):
        for j in range(1, len(self.activated_automata)):
            for i in range(0, j):
                vf_i = self.activated_automata[i][2]
                vf_j = self.activated_automata[j][2]

                print("Checking", i, j)
                print(vf_i)
                print(vf_j)

                cnt = 0
                for m in vf_i:
                    for n in vf_j:
                        mx, my = parse_field(m)
                        nx, ny = parse_field(n)
                        nei, lt = neigh(mx, my, nx, ny)
                        if nei:
                            cnt += 1
                            print(m, " -- ", n, " -- ", lt)

                if cnt > 0:
                    print(cnt, " dependencies found")

                


if __name__ == "__main__":
    from Automaton import load_pattern_matrix
    concept, matrix = load_pattern_matrix('test_files/square.pat')

    hoa = HOALearner(matrix, verbose=True)
    hoa.identify_base_automata()
    hoa.infere_automata_dependencies()




