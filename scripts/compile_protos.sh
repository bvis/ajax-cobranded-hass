#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PROTO_SRC="$PROJECT_ROOT/proto_src"
PROTO_OUT="$PROJECT_ROOT/custom_components/ajax_cobranded/proto"

if [ ! -d "$PROTO_SRC" ]; then
    echo "Error: proto_src/ directory not found at $PROTO_SRC"
    exit 1
fi

echo "Cleaning old generated files..."
find "$PROTO_OUT" -name '*_pb2.py' -o -name '*_pb2_grpc.py' -o -name '*_pb2.pyi' | xargs rm -f

echo "Compiling proto files..."
# Resolve protoc-gen-mypy from the active Python environment
MYPY_PLUGIN="$(python -c 'import sys; print(sys.prefix)')/bin/protoc-gen-mypy"

python -m grpc_tools.protoc \
    --proto_path="$PROTO_SRC" \
    --python_out="$PROTO_OUT" \
    --grpc_python_out="$PROTO_OUT" \
    --mypy_out="$PROTO_OUT" \
    --plugin="protoc-gen-mypy=${MYPY_PLUGIN}" \
    $(find "$PROTO_SRC" -name '*.proto')

echo "Proto compilation complete. Output: $PROTO_OUT"
