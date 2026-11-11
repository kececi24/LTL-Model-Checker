#pragma once

#include <vector>

struct State;
class Model;

class ModelGraph{
    private:
        std::vector<State*> nodes;
        std::vector<std::vector<short>> adjacency_graph; // Sorted list of states
        int initial_node_count; // First N elements of the list are initial nodes
    public:
        ModelGraph(Model&);
        std::vector<State*> BFS();
};