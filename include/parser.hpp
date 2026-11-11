#pragma once

#include <nlohmann/json.hpp>
#include <include/graph.hpp>

#include <string>
#include <vector>
#include <stdexcept>
#include <tuple>

const nlohmann::json model_schema = R"({
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["atomic_propositions", "initial_states", "states"],
  "additionalProperties": false,
  "properties": {
    "atomic_propositions": {
      "type": "array",
      "items": { "type": "string" }
    },
    "initial_states": {
      "type": "array",
      "items": { "type": "string" }
    },
    "states": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "required": ["labels", "transitions"],
        "additionalProperties": false,
        "properties": {
          "labels": { "type": "array", "items": { "type": "string" } },
          "transitions": { "type": "array", "items": { "type": "string" } }
        }
      }
    }
  }
})"_json;

struct State{
    std::string name;
    std::vector<std::string> labels;
    std::vector<State*> transitions;
};

class SemanticError : public std::runtime_error{
    public:
        explicit SemanticError(const std::string& message) : std::runtime_error("[SEMANTIC ERROR]: " + message) {};
};

class Model{
    private:
        std::vector<std::string> atomic_propositions;
        std::vector<State*> initial_states;
        std::vector<State> states;

        friend class ModelGraph;
    public:
        Model(const nlohmann::json&);
        int verify_semantic();
        int graph_explore();
        std::tuple<int, int> metrics();
};

