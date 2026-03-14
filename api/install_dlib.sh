#!/bin/bash
# install_dlib.sh - A portable script to install dlib with a fix for modern CMake (3.28+)
set -e

DLIB_VERSION="19.24.9"
DLIB_DIR="dlib-${DLIB_VERSION}"

# Determine portable sed -i command
if [[ "$OSTYPE" == "darwin"* ]]; then
    SED_CMD=(sed -i '')
else
    SED_CMD=(sed -i)
fi

echo "Cleaning up previous build artifacts..."
rm -rf dlib-*.tar.gz dlib-*/

echo "Downloading dlib ${DLIB_VERSION} source..."
pip download dlib==${DLIB_VERSION} --no-binary :all: --no-deps

# Extracting the source (handling possible extensions)
TARBALL=$(ls dlib-${DLIB_VERSION}.tar.*)
echo "Extracting ${TARBALL}..."
tar -xf "${TARBALL}"

echo "Patching pybind11 CMakeLists.txt for modern CMake compatibility..."
# Change VERSION 3.4 to 3.5 in pybind11's CMakeLists.txt
"${SED_CMD[@]}" 's/cmake_minimum_required(VERSION 3.4)/cmake_minimum_required(VERSION 3.5)/' "${DLIB_DIR}/dlib/external/pybind11/CMakeLists.txt"

echo "Building and installing dlib..."
pip install "./${DLIB_DIR}"

echo "Cleaning up..."
rm -rf "${DLIB_DIR}" "${TARBALL}"

echo "----------------------------------------------------"
echo "dlib ${DLIB_VERSION} has been installed successfully!"
echo "----------------------------------------------------"
