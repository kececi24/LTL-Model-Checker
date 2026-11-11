cmake_minimum_required(VERSION 3.15)
project(my_checker LANGUAGES CXX)

# Enforce C++17 standard for GCC
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Direct all compiled executable binaries to the project root directory,
# keeping all intermediate object and cache files inside build/
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}")
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_DEBUG "${CMAKE_SOURCE_DIR}")
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_SOURCE_DIR}")

# Portable static linking option for GCC on Windows (prevents missing libstdc++/libgcc DLL errors)
option(ENABLE_STATIC_RUNTIME "Statically link GCC runtime libraries for standalone binaries" ON)

# Project source files
set(SOURCES
    src/main.cpp
    src/parser.cpp
    src/graph.cpp
)

# Project header files
set(HEADERS
    include/graph.hpp
    include/parser.hpp
    include/valijson_nlohmann_bundled.hpp
    include/nlohmann/json.hpp
    include/nlohmann/json_fwd.hpp
)

# Main executable target
add_executable(my_checker ${SOURCES} ${HEADERS})

# Include paths:
#   - Root directory (for <include/...>)
#   - include/ directory (for <nlohmann/...>)
target_include_directories(my_checker PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# GCC compile and link flags
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(my_checker PRIVATE
        -Wall
        -Wextra
        -O2
    )

    # Static linking for standalone Windows GCC binaries
    if(WIN32 AND ENABLE_STATIC_RUNTIME AND CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
        target_link_options(my_checker PRIVATE -static -static-libgcc -static-libstdc++)
    endif()
endif()

# On Windows: create a shell script wrapper 'my_checker' in the root directory
# so that './my_checker --parse ...' succeeds in Git Bash, MSYS2, WSL, and Linux sh
# as strictly required by PDF Section 4 execution specification.
if(WIN32)
    add_custom_command(TARGET my_checker POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E echo "#!/bin/sh" > "${CMAKE_SOURCE_DIR}/my_checker"
        COMMAND ${CMAKE_COMMAND} -E echo "exec \"$$(dirname \"$$0\")/my_checker.exe\" \"$$@\"" >> "${CMAKE_SOURCE_DIR}/my_checker"
        COMMENT "Generated POSIX shell wrapper '${CMAKE_SOURCE_DIR}/my_checker' for Windows executable"
    )
endif()

# ---------------------------------------------------------------------------
# Cross-Platform Targets for Compiling Both Windows & Linux Binaries
# ---------------------------------------------------------------------------

# On Windows host: Build Linux ELF binary using WSL GCC
find_program(WSL_EXECUTABLE wsl)
if(WIN32 AND WSL_EXECUTABLE)
    add_custom_target(my_checker_linux
        COMMAND ${WSL_EXECUTABLE} -- /usr/bin/g++ -std=c++17 -O2 -I. -Iinclude src/main.cpp src/parser.cpp src/graph.cpp -o my_checker_linux
        WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
        COMMENT "Compiling 64-bit Linux ELF binary (my_checker_linux) using WSL GCC..."
    )

    add_custom_target(all_platforms
        DEPENDS my_checker my_checker_linux
        COMMENT "Successfully built both Windows (my_checker.exe) and Linux (my_checker_linux) in project root!"
    )
endif()

# On Linux host: Cross-compile Windows binary using MinGW-w64 if installed
if(UNIX AND NOT APPLE)
    find_program(MINGW_CXX x86_64-w64-mingw32-g++)
    if(MINGW_CXX)
        add_custom_target(my_checker_windows
            COMMAND ${MINGW_CXX} -std=c++17 -O2 -static -static-libgcc -static-libstdc++ -I. -Iinclude src/main.cpp src/parser.cpp src/graph.cpp -o "${CMAKE_SOURCE_DIR}/my_checker.exe"
            WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
            COMMENT "Cross-compiling Windows binary 'my_checker.exe' using MinGW-w64..."
        )

        add_custom_target(all_platforms
            DEPENDS my_checker my_checker_windows
            COMMENT "Successfully built both Linux (my_checker) and Windows (my_checker.exe) in project root!"
        )
    endif()
endif()
