#include <include/parser.hpp>
#include <nlohmann/json.hpp>

#include <iostream>
#include <string>
#include <fstream>
#include <tuple>

int main(int argc, char *argv[])
{
    std::string json_path;

    // Parse command-line arguments
    for (int i = 1; i < argc; ++i)
    {
        std::string arg = argv[i];
        if (arg == "--parse")
        {
            if (i + 1 < argc)
            {
                json_path = argv[++i]; // Grab the path following --parse
            }
            else
            {
                std::cerr << "[ERROR]: '--parse' requires a file path argument.\n";
                return 1;
            }
        }
        else
        {
            std::cerr << "[ERROR]: Unknown argument '" << arg << "'.\n";
            std::cerr << "Usage: " << argv[0] << " --parse <path_to_json_model>\n";
            return 1;
        }
    }

    if (json_path.empty())
    {
        std::cerr << "Usage: " << argv[0] << " --parse <path_to_json_model>\n";
        return 1;
    }

    try
    {
        std::ifstream file(json_path);
        if (!file.is_open())
        {
            std::cerr << "[ERROR]: Could not open file " << json_path << "\n";
            return 1;
        }

        nlohmann::json model_json = nlohmann::json::parse(file);
        std::cout << "[PARSER]: Loaded " << json_path << " successfully. \n";

        Model model(model_json);

        int state_count, transition_count;
        std::tie(state_count, transition_count) = model.metrics();
        std::cout << "[METRICS]: Total declared states: " << state_count;
        std::cout << "\n[METRICS]: Total transitions found: " << transition_count << "\n";

        model.verify_semantic();

        int unreachable_count = model.graph_explore();
        std::cout << "[REACHABILITY]: Reachable states from initial node(s): " << state_count - unreachable_count;
        std::cout << "\n[DIAGNOSTICS]: Unreachable states detected: " << unreachable_count << std::endl;
    }
    catch (const nlohmann::json::parse_error &e)
    {
        std::cerr << "[SYNTAX ERROR]: " << e.what() << std::endl;
        return 1;
    }
    catch (const SemanticError &e)
    {
        std::cerr << e.what() << std::endl;
        return 1;
    }
    catch (const std::exception &e)
    {
        std::cerr << e.what() << std::endl;
        return 1;
    }

    return 0;
}