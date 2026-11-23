cmake_minimum_required(VERSION 3.21)
project(UndercoverWiiNativeHostRuntime LANGUAGES CXX)

# Original-free native Wii host services. The proprietary PowerPC game
# AOT and owner DOL/ELF must never be checked into this target.
add_library(undercover_wii_host_runtime INTERFACE)
target_compile_features(undercover_wii_host_runtime INTERFACE cxx_std_20)
target_include_directories(undercover_wii_host_runtime INTERFACE "${CMAKE_CURRENT_SOURCE_DIR}")
target_sources(undercover_wii_host_runtime INTERFACE
    "${CMAKE_CURRENT_SOURCE_DIR}/wii_ipc_mailbox.h"
    "${CMAKE_CURRENT_SOURCE_DIR}/wii_hollywood_irq.h"
    "${CMAKE_CURRENT_SOURCE_DIR}/wii_ios_bus.h"
    "${CMAKE_CURRENT_SOURCE_DIR}/wii_stm_ios.h"
    "${CMAKE_CURRENT_SOURCE_DIR}/wii_guest_filesystem.h"
    "${CMAKE_CURRENT_SOURCE_DIR}/wii_sysconf_image.h"
    "${CMAKE_CURRENT_SOURCE_DIR}/wii_ios_yield_scheduler.h"
    "${CMAKE_CURRENT_SOURCE_DIR}/wii_nand_ios_reply_yield.h"
)
if(MSVC)
    target_compile_options(undercover_wii_host_runtime INTERFACE /W4 /WX)
else()
    target_compile_options(undercover_wii_host_runtime
        INTERFACE -Wall -Wextra -Werror)
endif()

include(CTest)
if(BUILD_TESTING)
    foreach(suite IN ITEMS
        wii_ipc_mailbox
        wii_hollywood_irq
        wii_ios_bus
        wii_stm_ios
        wii_guest_filesystem
        wii_sysconf_image
        wii_ios_yield_scheduler
        wii_nand_ios_reply_v374
    )
        add_executable("undercover_${suite}" "test_${suite}.cpp")
        target_link_libraries("undercover_${suite}" PRIVATE
            undercover_wii_host_runtime)
        add_test(NAME "undercover_${suite}" COMMAND "undercover_${suite}")
        set_tests_properties("undercover_${suite}" PROPERTIES TIMEOUT 30)
    endforeach()
endif()
