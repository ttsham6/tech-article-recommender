#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT_DIR}/infra/dist"

build_agent() {
  cd "${ROOT_DIR}/agent"
  rm -rf build/package build/dist build/strands-runtime.zip
  mkdir -p build/package
  uv build --wheel --out-dir build/dist
  uv pip install \
    --python-platform aarch64-manylinux2014 \
    --python-version 3.13 \
    --target build/package \
    --only-binary=:all: \
    build/dist/*.whl
  cp main.py build/package/
  (
    cd build/package
    zip -r ../strands-runtime.zip .
  )
  cp build/strands-runtime.zip "${DIST_DIR}/strands-runtime.zip"
}

build_api() {
  cd "${ROOT_DIR}/api"
  rm -rf build/package build/dist build/api-lambda.zip
  mkdir -p build/package
  uv build --wheel --out-dir build/dist
  uv pip install \
    --python-platform aarch64-manylinux2014 \
    --python-version 3.13 \
    --target build/package \
    --only-binary=:all: \
    build/dist/*.whl
  (
    cd build/package
    zip -r ../api-lambda.zip .
  )
  cp build/api-lambda.zip "${DIST_DIR}/api-lambda.zip"
}

mkdir -p "${DIST_DIR}"

build_agent
build_api
