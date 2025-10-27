#!/usr/bin/env python3
"""
Generate gRPC Python stubs from Protocol Buffer schema
Cross-platform Python version (Windows/Linux/macOS compatible)

Usage:
    python generate_grpc_stubs.py

Requirements:
    pip install grpcio-tools

Author: thc1006@ieee.org
Date: 2025-10-27
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("=" * 60)
    print("gRPC Stub Generation for SDR-O-RAN Connector")
    print("=" * 60)
    print()

    # Paths
    script_dir = Path(__file__).parent
    proto_dir = script_dir / "proto"
    output_dir = script_dir
    proto_file = proto_dir / "sdr_oran.proto"

    # Verify proto file exists
    if not proto_file.exists():
        print(f"❌ ERROR: Proto file not found: {proto_file}")
        sys.exit(1)

    # Install dependencies
    print("Installing dependencies...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q",
             "grpcio-tools", "protobuf", "numpy"],
            check=True
        )
        print("✅ Dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Warning: Could not install dependencies: {e}")
        print("   Continuing anyway (may already be installed)")

    print()
    print(f"Generating Python stubs from {proto_file.name}...")

    # Generate stubs
    try:
        subprocess.run(
            [
                sys.executable, "-m", "grpc_tools.protoc",
                f"-I{proto_dir}",
                f"--python_out={output_dir}",
                f"--grpc_python_out={output_dir}",
                f"--pyi_out={output_dir}",
                str(proto_file)
            ],
            check=True,
            capture_output=True,
            text=True
        )

        print()
        print("✅ SUCCESS: Generated stubs")
        print("   - sdr_oran_pb2.py (Protocol Buffer classes)")
        print("   - sdr_oran_pb2_grpc.py (gRPC service stubs)")
        print("   - sdr_oran_pb2.pyi (Type hints)")
        print()

        # Verify files exist
        pb2_file = output_dir / "sdr_oran_pb2.py"
        grpc_file = output_dir / "sdr_oran_pb2_grpc.py"
        pyi_file = output_dir / "sdr_oran_pb2.pyi"

        if pb2_file.exists() and grpc_file.exists():
            print(f"✅ Verification: All stub files present in {output_dir}")
            print()
            print("File sizes:")
            print(f"   - sdr_oran_pb2.py: {pb2_file.stat().st_size:,} bytes")
            print(f"   - sdr_oran_pb2_grpc.py: {grpc_file.stat().st_size:,} bytes")
            if pyi_file.exists():
                print(f"   - sdr_oran_pb2.pyi: {pyi_file.stat().st_size:,} bytes")

            print()
            print("Next steps:")
            print("   1. Review generated files")
            print("   2. Run: python test_grpc_connection.py")
            print("   3. Start server: python sdr_grpc_server.py")
            print("   4. Start client: python oran_grpc_client.py")
        else:
            print()
            print("⚠️  WARNING: Some stub files missing")
            sys.exit(1)

    except subprocess.CalledProcessError as e:
        print()
        print("❌ ERROR: Stub generation failed")
        print(f"   {e.stderr}")
        sys.exit(1)

    print()
    print("=" * 60)
    print("Stub generation complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
