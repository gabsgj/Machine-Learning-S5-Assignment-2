#include "types.hpp"
#include "embedding.hpp"
#include "json_loader.hpp"
#include "experiments.hpp"
#include <iostream>
#include <string>
#include <vector>

using namespace capability_embedding;

void printUsage(const char* progName) {
    std::cout << "Usage: " << progName << " [options]\n\n"
              << "Options:\n"
              << "  (no args)          Run default capability embedding summary\n"
              << "  --all              Run complete suite (vectors, compatibility, composition, all 5 experiments)\n"
              << "  --experiments      Run all five formal experiments (Sections 7.1 - 7.5)\n"
              << "  --vectors          Display structured vector embeddings for states, goals, and capabilities\n"
              << "  --compatibility    Display pairwise capability compatibility matrix\n"
              << "  --composition      Display sequential capability composition demonstration\n"
              << "  --help, -h         Display this help message\n";
}

int main(int argc, char* argv[]) {
    std::string basicDataPath = "data/ecommerce_basic.json";
    std::string altDataPath = "data/alternative_implementations.json";

    bool runAll = false;
    bool runExp = false;
    bool showVectors = false;
    bool showCompat = false;
    bool showComp = false;

    if (argc == 1) {
        // Default execution: run standard summary and key experiments
        runExp = true;
    } else {
        for (int i = 1; i < argc; ++i) {
            std::string arg = argv[i];
            if (arg == "--all") {
                runAll = true;
            } else if (arg == "--experiments") {
                runExp = true;
            } else if (arg == "--vectors") {
                showVectors = true;
            } else if (arg == "--compatibility") {
                showCompat = true;
            } else if (arg == "--composition") {
                showComp = true;
            } else if (arg == "--help" || arg == "-h") {
                printUsage(argv[0]);
                return 0;
            } else {
                std::cerr << "Unknown option: " << arg << "\n";
                printUsage(argv[0]);
                return 1;
            }
        }
    }

    std::cout << "======================================================================\n";
    std::cout << "PCCST503 MACHINE LEARNING: ASSIGNMENT 2\n";
    std::cout << "Design of a Vector Embedding for Capability Composition\n";
    std::cout << "Domain: E-Commerce Formal Application Model\n";
    std::cout << "======================================================================\n";

    // 1. Initialize Engine & Load Dataset
    VectorEmbeddingEngine engine;
    ApplicationProblem app;
    std::vector<Capability> allCaps;

    try {
        app = JsonLoader::loadApplication(basicDataPath);
        auto altCaps = JsonLoader::loadCapabilities(altDataPath);
        allCaps = app.capabilities;
        allCaps.insert(allCaps.end(), altCaps.begin(), altCaps.end());
    } catch (const std::exception& e) {
        std::cerr << "Fatal Error loading datasets: " << e.what() << "\n";
        return 1;
    }

    std::cout << "Loaded Problem: " << app.applicationName << " (Domain: " << app.domain << ")\n";
    std::cout << "State Universe Dimension:      " << engine.stateDimension() << " canonical boolean variables\n";
    std::cout << "Capability Vector Dimension:  " << engine.capabilityDimension()
              << " (11 pre + 11 eff + 6 type + 2 I/O + 6 QoS)\n";
    std::cout << "Total Capabilities in Dataset: " << allCaps.size() << " ("
              << app.capabilities.size() << " core, " << (allCaps.size() - app.capabilities.size()) << " extended)\n";

    if (runAll || showVectors) {
        BenchmarkExperiments::printVectorRepresentations(app, engine);
    }

    if (runAll || showCompat) {
        BenchmarkExperiments::printCompatibilityMatrix(app.capabilities, engine);
    }

    if (runAll || showComp) {
        BenchmarkExperiments::runExperiment2(app, engine);
    }

    if (runAll || runExp) {
        BenchmarkExperiments::runExperiment1(app, engine);
        if (!showComp) BenchmarkExperiments::runExperiment2(app, engine);
        BenchmarkExperiments::runExperiment3(allCaps, engine);
        BenchmarkExperiments::runExperiment4(app, allCaps, engine);
        BenchmarkExperiments::runExperiment5(allCaps, engine);
    }

    std::cout << "\nExecution completed successfully.\n";
    return 0;
}
