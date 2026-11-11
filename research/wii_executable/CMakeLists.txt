cmake_minimum_required(VERSION 3.16)

# Source-only native host build of selected reconstructed Wii physics code.
# This does not compile, link, emulate, or distribute Nintendo/EA binaries.
project(nfsuc_wii_physics_host LANGUAGES CXX)

add_library(nfsuc_wii_physics STATIC
    attrib_text.cpp
    attrib_tweak.cpp
    attrib_memory.cpp
    wii_vehicle_snapshot.cpp
    wii_rigidbody_controls.cpp
    wii_rigidbody_orientation.cpp
    wii_rigidbody_final_transform.cpp
    wii_rigidbody_frame.cpp
    wii_rigidbody_endframe.cpp
    wii_rigidbody_sleep.cpp
    wii_rigidbody_resolve.cpp
    wii_rigidbody_transform.cpp
    wii_rigidbody_drag.cpp
    wii_rigidbody_detach.cpp
    wii_rigidbody_primitive.cpp
)
target_compile_features(nfsuc_wii_physics PUBLIC cxx_std_17)
target_include_directories(nfsuc_wii_physics PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

add_executable(nfsuc_physics_smoke pc_physics_smoke.cpp)
target_link_libraries(nfsuc_physics_smoke PRIVATE nfsuc_wii_physics)
target_compile_features(nfsuc_physics_smoke PRIVATE cxx_std_17)

enable_testing()
add_test(NAME nfsuc_host_two_frame_physics COMMAND nfsuc_physics_smoke --steps 2)
add_test(NAME nfsuc_host_four_frame_physics COMMAND nfsuc_physics_smoke --steps 4)

add_executable(nfsuc_primitive_regressions test_wii_rigidbody_primitive.cpp)
target_link_libraries(nfsuc_primitive_regressions PRIVATE nfsuc_wii_physics)
target_compile_features(nfsuc_primitive_regressions PRIVATE cxx_std_17)
add_test(NAME nfsuc_wii_primitive_world_transform COMMAND nfsuc_primitive_regressions)
