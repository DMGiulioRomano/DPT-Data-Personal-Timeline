file(REMOVE_RECURSE ${CMAKE_BINARY_DIR}/venv)
file(GLOB_RECURSE CACHE_FILES "${CMAKE_SOURCE_DIR}/src/*.pyc")
file(REMOVE ${CACHE_FILES})
file(GLOB_RECURSE PYCACHE_DIRS "${CMAKE_SOURCE_DIR}/src/__pycache__")
file(REMOVE_RECURSE ${PYCACHE_DIRS})