cmake_minimum_required(VERSION 3.14)
project(CapabilityCompositionFramework LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(include)

# Main Library Sources
set(LIB_SOURCES
    src/Capability.cpp
    src/Embedding.cpp
)

# Main Executable
add_executable(capability_app src/main.cpp ${LIB_SOURCES})

# Test / Experiment Suite Executable
add_executable(run_experiments tests/run_experiments.cpp ${LIB_SOURCES})