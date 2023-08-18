# Meta-cognitive machines
#
# Learning engine deals with learning functionalities considering
# long-term automata memory
#
# Authors: {svc, lucy}@dmi.uns.ac.rs

from UnsupervisedLearning import UnsupervisedLearner
from SupervisedLearning import SupervisedLearner

class LearningEngine:
    def __init__(self, automata_memory, verbose=False):
        self.automata_memory = automata_memory
        self.verbose = verbose


    def learn(self, input_file):
        print("Activated learning for", input_file)
        supervised_learning = True if input_file.endswith('.pat') else False
        if supervised_learning:
            self.slearn(input_file)
        else:
            self.ulearn(input_file)


    def slearn(self, input_file):
        sl = SupervisedLearner(input_file, self.automata_memory, verbose=self.verbose)
        sl.learn_concept()


    def ulearn(self, input_file):
        ul = UnsupervisedLearner(input_file, self.automata_memory, verbose=self.verbose)
        ul.identify_and_learn_unknown_concepts()


if __name__ == "__main__":
    from AutomataMemory import AutomataMemory
    from Matrix import load_matrix
    from InferenceEngine import hoa_inference

    automata_memory = AutomataMemory()

    le = LearningEngine(automata_memory, verbose=False)
    le.learn('test_files/vertical_line.pat')
    le.learn('test_files/horizontal_line.pat')
    le.learn('test_files/left_angle.pat')
    le.learn('test_files/right_angle.pat')
    le.learn('test_files/square.pat')
    le.learn('test_files/scene-rect.txt')
    le.learn('test_files/square.pat')
    le.learn('test_files/rect.pat')
    le.learn('test_files/square_cross.pat')
    le.learn('test_files/triangle.pat')

    print("Learning finished")

    print("\n\n\nAutomata memory")
    automata_memory.info()

   
    print("\n\nRECOGNITION TEST")

    scene_desc, scene_matrix = load_matrix('test_files/scene4.txt')
    hoa_inference('test_files/scene4.txt', automata_memory, show_activation_history=False)
    