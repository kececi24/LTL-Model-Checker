#define VALIJSON_USE_EXCEPTIONS 1

#include <include/parser.hpp>
#include <nlohmann/json.hpp>
#include <include/valijson_nlohmann_bundled.hpp>
#include <include/graph.hpp>

#include <string>
#include <vector>
#include <stdexcept>
#include <unordered_set>
#include <tuple>

Model::Model(const nlohmann::json& jdata){

    // Validate json schema
    valijson::Schema schema;
    valijson::SchemaParser parser(valijson::SchemaParser::kDraft7);

    valijson::adapters::NlohmannJsonAdapter schemaAdapter(model_schema);
    parser.populateSchema(schemaAdapter, schema);

    valijson::Validator validator;
    valijson::adapters::NlohmannJsonAdapter documentAdapter(jdata);
    valijson::ValidationResults results;

    if(!validator.validate(schema, documentAdapter, &results)){
        valijson::ValidationResults::Error error;

        if(results.popError(error)){
            throw std::invalid_argument("[SCHEMA ERROR]: Invalid model at " + error.jsonPointer + ": " + error.description);
        }

        throw std::invalid_argument("[SCHEMA ERROR]: Invalid model JSON");
    }

    // Convert json to model
    const std::string ap_key = "atomic_propositions";
    const std::string s_key = "states";
    const std::string labels_key = "labels";
    const std::string trans_key = "transitions";
    const std::string init_key = "initial_states";

    if(jdata.contains(ap_key)){
        for(const auto& ap : jdata[ap_key]){
            atomic_propositions.push_back(ap.get<std::string>());
        }
    }

    if(jdata.contains(s_key)){
        states.reserve(jdata[s_key].size());
    }

    std::unordered_map<std::string, size_t> state_indices;

    for(auto& [name, state_data] : jdata[s_key].items()){
        State s;
        s.name = name;

        if(state_data.contains(labels_key)){
            for(const auto& lbl : state_data[labels_key]){
                s.labels.push_back(lbl.get<std::string>());
            }
        }

        states.push_back(std::move(s));
        state_indices[name] = states.size() - 1;
    }

    for(auto& [name, state_data] : jdata[s_key].items()){
        State& current_state = states[state_indices[name]];

        if(state_data.contains(trans_key)){
            for(const auto& target_json : state_data[trans_key]){
                std::string target_name = target_json.get<std::string>();
 
                if(state_indices.count(target_name)){
                    current_state.transitions.push_back(&states[state_indices[target_name]]);
                }                
            }
        }
    }

    if(jdata.contains(init_key)){
        for(const auto& init_name_json : jdata[init_key]){
            std::string init_name = init_name_json.get<std::string>();
            if(state_indices.count(init_name)){
                initial_states.push_back(&states[state_indices[init_name]]);
            }
        }
    }
}

int Model::verify_semantic(){
    if(std::adjacent_find(atomic_propositions.begin(), atomic_propositions.end()) != atomic_propositions.end())
        throw SemanticError("Duplicate atomic propositions specified.");
    
    if(std::adjacent_find(initial_states.begin(), initial_states.end()) != initial_states.end())
        throw SemanticError("Duplicate initial states specified.");

    std::unordered_set<std::string> valid_aps(atomic_propositions.begin(), atomic_propositions.end());

    if(initial_states.empty())
        throw SemanticError("No initial states specified.");
    if(states.empty())
        throw SemanticError("No states specified.");

    // Validate labels and transitions
    for(const auto& state : states){
        std::unordered_set<std::string> seen_labels;
        for(const auto& label : state.labels){
             if(!seen_labels.insert(label).second)
                throw SemanticError("State: " + state.name + " has duplicate label: " + label);
            if(valid_aps.find(label) == valid_aps.end()) 
                throw SemanticError("State: " + state.name + " has undeclared atomic proposition label: " + label);
        }
        
        if (state.transitions.empty())
            throw SemanticError("State: " + state.name + " is in a deadlock and has no outgoing transitions.");
        
        std::unordered_set<const State*> seen_targets;
        for(const auto& target : state.transitions){
            if(target == nullptr)
                throw SemanticError("State: " + state.name + " has an undefined transition.");
            if(!seen_targets.insert(target).second)
                throw SemanticError("State: " + state.name + "has duplicate transition to: " + target->name);
        }
    }

    return 0;
}

int Model::graph_explore(){
    ModelGraph graph(*this);
    auto unreachable_set = graph.BFS();
    return unreachable_set.size();
}

std::tuple<int, int> Model::metrics(){
    int state_count = states.size();
    int transition_count = 0;
    for(const auto& state : states){
        transition_count += state.transitions.size();
    }

    return std::make_tuple(state_count, transition_count);
}