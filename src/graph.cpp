#include <include/graph.hpp>
#include <include/parser.hpp>

#include <unordered_set>
#include <unordered_map>
#include <queue>
#include <algorithm>

ModelGraph::ModelGraph(Model& model){
    std::unordered_set<const State*> init_set(model.initial_states.begin(), model.initial_states.end());

    initial_node_count = static_cast<int>(model.initial_states.size());
    nodes.reserve(model.states.size());

    for(State* init_state : model.initial_states){
        nodes.push_back(init_state);
    }

    for(State& st : model.states){
        if(init_set.find(&st) == init_set.end())
            nodes.push_back(&st);
    }

    std::unordered_map<State*, short> state_to_index;
    for(size_t i = 0; i < nodes.size(); ++i){
        state_to_index[nodes[i]] = static_cast<short>(i);
    }

    adjacency_graph.resize(nodes.size());
    for(size_t i = 0; i < nodes.size(); ++i){
        for(State* target : nodes[i]->transitions){
            auto it = state_to_index.find(target);
            if(it != state_to_index.end()){
                adjacency_graph[i].push_back(it->second);
            }
        }

        std::sort(adjacency_graph[i].begin(), adjacency_graph[i].end());
    }
}

std::vector<State*> ModelGraph::BFS(){
    size_t n = nodes.size();
    std::vector<bool> visited(n, false);
    std::queue<short> q;

    for(int i = 0; i < initial_node_count; i++){
        visited[i] = true;
        q.push(static_cast<short>(i));
    }

    while(!q.empty()){
        short curr = q.front();
        q.pop();

        for(short neighbor : adjacency_graph[curr]){
            if(!visited[neighbor]){
                visited[neighbor] = true;
                q.push(neighbor);
            }
        }
    }

    std::vector<State*> unreachable_set;
    for(size_t i = 0; i < n; i++){
        if(!visited[i])
            unreachable_set.push_back(nodes[i]);
    }

    return unreachable_set;
}