cmake_minimum_required(VERSION 3.16)
project(cascade-mis CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native -funroll-loops -DNDEBUG")

add_library(misgraph src/graph.cpp)

add_executable(cascade src/main.cpp src/cascade.cpp src/exact.cpp)
target_link_libraries(cascade misgraph)

add_executable(mis-convert tools/mis_convert.cpp)
target_link_libraries(mis-convert misgraph)

add_executable(mis-verify tools/mis_verify.cpp)
target_link_libraries(mis-verify misgraph)
