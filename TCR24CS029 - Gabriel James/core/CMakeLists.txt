cmake_minimum_required(VERSION 3.16)
project(careweave_mini_core VERSION 1.0.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_C_STANDARD 99)

# The efficiency numbers of the evaluation harness describe an optimized build, so a plain
# configure of this directory defaults to Release; an explicit -DCMAKE_BUILD_TYPE still wins.
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type (default Release)" FORCE)
endif()

# Warnings that this project controls. Third-party headers are included with SYSTEM so their
# diagnostics never enter the build log; project sources must compile clean under these flags.
set(CAREWEAVE_WARNINGS -Wall -Wextra -Wpedantic -Wshadow -Wconversion -Wsign-conversion)

option(CAREWEAVE_BUILD_TESTS "Build the CTest suites" ON)
option(CAREWEAVE_BUILD_SQLITE "Compile the vendored SQLite amalgamation into the core" ON)

set(CAREWEAVE_THIRD_PARTY_DIR ${CMAKE_CURRENT_SOURCE_DIR}/third_party)

# ---- Vendored SQLite amalgamation (public domain, version 3.46.1) ----
if(CAREWEAVE_BUILD_SQLITE)
  add_library(careweave_sqlite STATIC ${CAREWEAVE_THIRD_PARTY_DIR}/sqlite/sqlite3.c)
  target_include_directories(careweave_sqlite SYSTEM PUBLIC ${CAREWEAVE_THIRD_PARTY_DIR}/sqlite)
  # The amalgamation is generated code; silence its diagnostics instead of editing it.
  target_compile_options(careweave_sqlite PRIVATE -w)
  find_library(COREFOUNDATION_LIBRARY CoreFoundation)
  if(COREFOUNDATION_LIBRARY)
    target_link_libraries(careweave_sqlite PUBLIC ${COREFOUNDATION_LIBRARY})
  endif()
endif()

# ---- Core library: one static library, sources grouped per concern ----
file(GLOB CAREWEAVE_CORE_SOURCES
  src/core/*.cpp
  src/spec/*.cpp
  src/embedding/*.cpp
  src/compat/*.cpp
  src/mapper/*.cpp
  src/adapter/*.cpp
  src/composer/*.cpp
  src/planner/*.cpp
  src/gateway/*.cpp
  src/bundle/*.cpp
  src/util/*.cpp
)

add_library(careweave_mini_core STATIC ${CAREWEAVE_CORE_SOURCES})
target_include_directories(careweave_mini_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_include_directories(careweave_mini_core SYSTEM PUBLIC
  ${CAREWEAVE_THIRD_PARTY_DIR}
  ${CAREWEAVE_THIRD_PARTY_DIR}/httplib
  ${CAREWEAVE_THIRD_PARTY_DIR}/nlohmann
  ${CAREWEAVE_THIRD_PARTY_DIR}/sqlite
)
target_compile_options(careweave_mini_core PRIVATE ${CAREWEAVE_WARNINGS})

if(CAREWEAVE_BUILD_SQLITE)
  target_link_libraries(careweave_mini_core PUBLIC careweave_sqlite)
endif()
find_package(Threads REQUIRED)
target_link_libraries(careweave_mini_core PUBLIC Threads::Threads)

# ---- Command line front end: specification tooling and, later, the pipeline commands ----
add_executable(careweave_cli cli/main.cpp)
target_link_libraries(careweave_cli PRIVATE careweave_mini_core)
target_compile_options(careweave_cli PRIVATE ${CAREWEAVE_WARNINGS})
set_target_properties(careweave_cli PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})

# ---- Gateway front end: management API, canonical hospital API, workflows, dashboard ----
add_executable(careweave_gateway cli/gateway_main.cpp)
target_link_libraries(careweave_gateway PRIVATE careweave_mini_core)
target_compile_options(careweave_gateway PRIVATE ${CAREWEAVE_WARNINGS})
set_target_properties(careweave_gateway PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})

# ---- Test suites: one executable per tests/test_*.cpp, registered with ctest ----
if(CAREWEAVE_BUILD_TESTS)
  enable_testing()
  file(GLOB CAREWEAVE_TEST_SOURCES ${CMAKE_CURRENT_SOURCE_DIR}/tests/test_*.cpp)
  foreach(TEST_SOURCE ${CAREWEAVE_TEST_SOURCES})
    get_filename_component(TEST_NAME ${TEST_SOURCE} NAME_WE)
    add_executable(${TEST_NAME} ${TEST_SOURCE})
    target_link_libraries(${TEST_NAME} PRIVATE careweave_mini_core)
    target_include_directories(${TEST_NAME} PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
    # The adapter suite compiles an emitted translation unit against the public headers, so the
    # tests know where the source tree lives.
    target_compile_definitions(${TEST_NAME} PRIVATE
      CAREWEAVE_CORE_DIR="${CMAKE_CURRENT_SOURCE_DIR}")
    set_target_properties(${TEST_NAME} PROPERTIES
      RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/tests)
    add_test(NAME ${TEST_NAME} COMMAND ${TEST_NAME})
  endforeach()
endif()

# ---- Experiments and evaluation harness (same build tree, same warnings) ----
option(CAREWEAVE_BUILD_EXPERIMENTS "Build the experiment programs and the evaluation harness" ON)
if(CAREWEAVE_BUILD_EXPERIMENTS)
  add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../experiments ${CMAKE_BINARY_DIR}/experiments)
endif()

message(STATUS "CareWeave Mini core: C++${CMAKE_CXX_STANDARD}, warnings ${CAREWEAVE_WARNINGS}")
