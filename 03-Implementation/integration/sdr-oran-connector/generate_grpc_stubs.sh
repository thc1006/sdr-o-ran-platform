#!/bin/bash
# Generate gRPC Python stubs from Protocol Buffer schema
#
# Usage: bash generate_grpc_stubs.sh
#
# Requirements:
#   pip install grpcio-tools
#
# Author: thc1006@ieee.org
# Date: 2025-10-27

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROTO_DIR="$SCRIPT_DIR/proto"
OUTPUT_DIR="$SCRIPT_DIR"

echo "============================================================"
echo "gRPC Stub Generation for SDR-O-RAN Connector"
echo "============================================================"
echo ""

# Check if protoc is available
if ! command -v python &> /dev/null; then
    echo "ERROR: Python not found. Please install Python 3.8+"
    exit 1
fi

# Install grpcio-tools if not present
echo "Installing grpcio-tools..."
pip install grpcio-tools protobuf numpy --quiet

# Generate Python stubs
echo ""
echo "Generating Python stubs from sdr_oran.proto..."
python -m grpc_tools.protoc \
    -I"$PROTO_DIR" \
    --python_out="$OUTPUT_DIR" \
    --grpc_python_out="$OUTPUT_DIR" \
    --pyi_out="$OUTPUT_DIR" \
    "$PROTO_DIR/sdr_oran.proto"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS: Generated stubs"
    echo "   - sdr_oran_pb2.py (Protocol Buffer classes)"
    echo "   - sdr_oran_pb2_grpc.py (gRPC service stubs)"
    echo "   - sdr_oran_pb2.pyi (Type hints)"
    echo ""
    echo "Files created in: $OUTPUT_DIR"

    # Verify files exist
    if [ -f "$OUTPUT_DIR/sdr_oran_pb2.py" ] && [ -f "$OUTPUT_DIR/sdr_oran_pb2_grpc.py" ]; then
        echo ""
        echo "✅ Verification: All stub files present"

        # Show file sizes
        echo ""
        echo "File sizes:"
        ls -lh "$OUTPUT_DIR/sdr_oran_pb2.py" | awk '{print "   - sdr_oran_pb2.py: " $5}'
        ls -lh "$OUTPUT_DIR/sdr_oran_pb2_grpc.py" | awk '{print "   - sdr_oran_pb2_grpc.py: " $5}'

        echo ""
        echo "Next steps:"
        echo "   1. Review generated files"
        echo "   2. Uncomment imports in sdr_grpc_server.py and oran_grpc_client.py"
        echo "   3. Test with: python sdr_grpc_server.py"
    else
        echo ""
        echo "⚠️  WARNING: Some stub files missing"
        exit 1
    fi
else
    echo ""
    echo "❌ ERROR: Stub generation failed"
    exit 1
fi

echo ""
echo "============================================================"
echo "Stub generation complete!"
echo "============================================================"
