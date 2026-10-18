cmake_minimum_required(VERSION 3.12)
project(CapabilityEmbedding VERSION 1.0.0 LANGUAGES CXX)

# Require C++17
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Include directory
include_directories(include)

# Compile options & warnings
if(MSVC)
    add_compile_options(/W4 /permissive-)
else()
    add_compile_options(-Wall -Wextra -pedantic)
endif()

# Core static library
add_library(capability_embedding STATIC
    src/Embedding.cpp
)

target_include_directories(capability_embedding PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

# Main executable
add_executable(flight_booking_embedding
    src/main.cpp
)

target_link_libraries(flight_booking_embedding PRIVATE
    capability_embedding
)
