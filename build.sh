#!/usr/bin/env bash


# Get script directory using https://stackoverflow.com/a/246128
get_source_dir () {
    local SOURCE="${BASH_SOURCE[0]}"
    while [ -h "$SOURCE" ]; do
    local TARGET="$(readlink "$SOURCE")"
    if [[ $TARGET == /* ]]; then
        # echo "SOURCE '$SOURCE' is an absolute symlink to '$TARGET'"
        SOURCE="$TARGET"
    else
        local DIR="$( dirname "$SOURCE" )"
        # echo "SOURCE '$SOURCE' is a relative symlink to '$TARGET' (relative to '$DIR')"
        SOURCE="$DIR/$TARGET"
    fi
    done
    # echo "SOURCE is '$SOURCE'"
    local RDIR="$( dirname "$SOURCE" )"
    DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
    echo "$DIR"
}

PLATFORM="$(uname)"

SOURCE_DIR="$(get_source_dir)"

git submodule update --init --recursive

cd lib/bluezero && mkdir -p build && cd build

if [[ "$PLATFORM" == "Darwin" ]] &&  command -v brew >/dev/null 2>&1 ; then
    echo "Assuming brew was used to install Qt5"
    cmake -DCMAKE_BUILD_TYPE=Debug -DBUILD_GUI=ON -DBUILD_EXAMPLES=ON \
        -DCMAKE_PREFIX_PATH=$(brew --prefix qt) \
        -DCMAKE_LIBRARY_OUTPUT_DIRECTORY=$SOURCE_DIR/src/vrep_gym/b0/ \
        .. && \
    cmake --build . --config Debug --target b0 -- -j4
else
    echo "Going to assume Qt5 can be found by CMake using default configuration"
    cmake -DCMAKE_BUILD_TYPE=Debug -DBUILD_GUI=ON -DBUILD_EXAMPLES=ON \
        -DCMAKE_LIBRARY_OUTPUT_DIRECTORY=$SOURCE_DIR/src/vrep_gym/b0/ \
        .. && \
    cmake --build . --config Debug --target b0 -- -j4
fi
cd $SOURCE_DIR




