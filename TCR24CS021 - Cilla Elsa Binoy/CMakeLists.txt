cmake_minimum_required(VERSION 3.15)
project(CapabilityEmbedding LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(capability_embedding
    src/Embedding.cpp
)

target_include_directories(capability_embedding PUBLIC include)

if (MSVC)
    target_compile_options(capability_embedding PRIVATE /W4)
else()
    target_compile_options(capability_embedding PRIVATE -Wall -Wextra -pedantic)
endif()

add_executable(test_embedding
    tests/test_embedding.cpp
)

target_link_libraries(test_embedding PRIVATE capability_embedding)

if (MSVC)
    target_compile_options(test_embedding PRIVATE /W4)
else()
    target_compile_options(test_embedding PRIVATE -Wall -Wextra -pedantic)
endif()
