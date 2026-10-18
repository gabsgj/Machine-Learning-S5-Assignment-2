# Experiment programs and the evaluation harness.
#
# This directory is included from core/CMakeLists.txt so one configure step builds the library,
# the CLI, the test suites, the five experiments and the evaluation harness. Each experiment is
# a standalone program with assertion based exit codes; the harness reuses the same support
# library. All outputs are written under experiments/out/ by default.

get_filename_component(CAREWEAVE_ROOT_DIR ${CMAKE_CURRENT_SOURCE_DIR} DIRECTORY)

add_library(careweave_experiment_support STATIC ${CMAKE_CURRENT_SOURCE_DIR}/src/experiment_support.cpp)
target_link_libraries(careweave_experiment_support PUBLIC careweave_mini_core)
target_include_directories(careweave_experiment_support PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src)
target_compile_definitions(careweave_experiment_support PUBLIC CAREWEAVE_ROOT="${CAREWEAVE_ROOT_DIR}")
target_compile_options(careweave_experiment_support PRIVATE ${CAREWEAVE_WARNINGS})

file(GLOB CAREWEAVE_EXPERIMENT_MAINS ${CMAKE_CURRENT_SOURCE_DIR}/src/exp[0-9]*.cpp)
foreach(EXPERIMENT_SOURCE ${CAREWEAVE_EXPERIMENT_MAINS})
  get_filename_component(EXPERIMENT_NAME ${EXPERIMENT_SOURCE} NAME_WE)
  add_executable(${EXPERIMENT_NAME} ${EXPERIMENT_SOURCE})
  target_link_libraries(${EXPERIMENT_NAME} PRIVATE careweave_experiment_support)
  target_compile_options(${EXPERIMENT_NAME} PRIVATE ${CAREWEAVE_WARNINGS})
  set_target_properties(${EXPERIMENT_NAME} PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/experiments)
endforeach()

set(CAREWEAVE_EVALUATION_SOURCE ${CMAKE_CURRENT_SOURCE_DIR}/evaluation/evaluation.cpp)
if(EXISTS ${CAREWEAVE_EVALUATION_SOURCE})
  add_executable(careweave_evaluation ${CAREWEAVE_EVALUATION_SOURCE})
  target_link_libraries(careweave_evaluation PRIVATE careweave_experiment_support)
  target_compile_options(careweave_evaluation PRIVATE ${CAREWEAVE_WARNINGS})
  set_target_properties(careweave_evaluation PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/experiments)
endif()

message(STATUS "CareWeave Mini experiments: ${CAREWEAVE_EXPERIMENT_MAINS}")
