cmake_minimum_required(VERSION 3.10)
project(tgp_calculator CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

add_executable(tgp_calculator
    main.cpp
    calculator.cpp
)

target_compile_options(tgp_calculator PRIVATE -Wall -Wextra -O2)

install(TARGETS tgp_calculator DESTINATION bin)
