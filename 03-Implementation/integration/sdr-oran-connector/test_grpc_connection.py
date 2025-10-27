#!/usr/bin/env python3
"""
Test gRPC connection and stub generation
Verifies that sdr_oran_pb2.py and sdr_oran_pb2_grpc.py were generated correctly

Usage:
    # First generate stubs:
    python generate_grpc_stubs.py

    # Then run this test:
    python test_grpc_connection.py

Author: thc1006@ieee.org
Date: 2025-10-27
"""

import sys
import time
from pathlib import Path

def test_imports():
    """Test that generated stubs can be imported"""
    print("=" * 60)
    print("Test 1: Import Generated Stubs")
    print("=" * 60)

    try:
        import sdr_oran_pb2
        print("✅ Successfully imported sdr_oran_pb2")
    except ImportError as e:
        print(f"❌ Failed to import sdr_oran_pb2: {e}")
        print("   Run: python generate_grpc_stubs.py")
        return False

    try:
        import sdr_oran_pb2_grpc
        print("✅ Successfully imported sdr_oran_pb2_grpc")
    except ImportError as e:
        print(f"❌ Failed to import sdr_oran_pb2_grpc: {e}")
        print("   Run: python generate_grpc_stubs.py")
        return False

    print()
    return True


def test_message_creation():
    """Test creating Protocol Buffer messages"""
    print("=" * 60)
    print("Test 2: Create Protocol Buffer Messages")
    print("=" * 60)

    try:
        import sdr_oran_pb2
        import numpy as np

        # Create IQSampleBatch
        batch = sdr_oran_pb2.IQSampleBatch(
            station_id="test-station",
            band="Ku-band",
            timestamp_ns=int(time.time() * 1e9),
            sequence_number=1,
            center_frequency_hz=12.5e9,
            sample_rate=10e6,
            samples=[1.0, 0.5, -0.3, 0.8] * 1024,  # 4096 samples
            snr_db=15.5,
            receive_power_dbm=-75.0,
            agc_locked=True,
            doppler_shift_hz=12500.0,
            timing_offset_ns=125
        )

        print(f"✅ Created IQSampleBatch:")
        print(f"   - Station: {batch.station_id}")
        print(f"   - Band: {batch.band}")
        print(f"   - Center Frequency: {batch.center_frequency_hz/1e9:.4f} GHz")
        print(f"   - Sample Rate: {batch.sample_rate/1e6:.2f} MSPS")
        print(f"   - Samples: {len(batch.samples)} values")
        print(f"   - SNR: {batch.snr_db:.1f} dB")
        print(f"   - Doppler Shift: {batch.doppler_shift_hz:.1f} Hz")

        # Create StreamStatsRequest
        stats_req = sdr_oran_pb2.StreamStatsRequest(
            station_id="test-station"
        )

        print(f"\n✅ Created StreamStatsRequest:")
        print(f"   - Station: {stats_req.station_id}")

        # Create DopplerUpdate
        doppler_update = sdr_oran_pb2.DopplerUpdate(
            station_id="test-station",
            doppler_shift_hz=15000.0,
            doppler_rate_hz_per_sec=250.0
        )

        print(f"\n✅ Created DopplerUpdate:")
        print(f"   - Station: {doppler_update.station_id}")
        print(f"   - Doppler Shift: {doppler_update.doppler_shift_hz:.1f} Hz")
        print(f"   - Doppler Rate: {doppler_update.doppler_rate_hz_per_sec:.1f} Hz/s")

        print()
        return True

    except Exception as e:
        print(f"❌ Failed to create messages: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_service_stub():
    """Test that gRPC service stub exists"""
    print("=" * 60)
    print("Test 3: Verify gRPC Service Stub")
    print("=" * 60)

    try:
        import sdr_oran_pb2_grpc

        # Check that IQStreamServiceStub exists
        assert hasattr(sdr_oran_pb2_grpc, 'IQStreamServiceStub')
        print("✅ IQStreamServiceStub exists")

        # Check that IQStreamServiceServicer exists
        assert hasattr(sdr_oran_pb2_grpc, 'IQStreamServiceServicer')
        print("✅ IQStreamServiceServicer exists")

        # List methods
        stub_methods = [m for m in dir(sdr_oran_pb2_grpc.IQStreamServiceStub)
                       if not m.startswith('_')]
        print(f"\n✅ Stub methods available:")
        for method in stub_methods:
            print(f"   - {method}")

        print()
        return True

    except AssertionError as e:
        print(f"❌ Service stub incomplete: {e}")
        return False
    except Exception as e:
        print(f"❌ Failed to verify service stub: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_serialization():
    """Test Protocol Buffer serialization"""
    print("=" * 60)
    print("Test 4: Test Serialization/Deserialization")
    print("=" * 60)

    try:
        import sdr_oran_pb2

        # Create message
        original = sdr_oran_pb2.IQSampleBatch(
            station_id="serialize-test",
            band="Ka-band",
            timestamp_ns=123456789000,
            sequence_number=42,
            center_frequency_hz=28e9,
            sample_rate=50e6,
            samples=[0.1, 0.2, 0.3, 0.4],
            snr_db=20.5
        )

        # Serialize
        serialized = original.SerializeToString()
        print(f"✅ Serialized message: {len(serialized)} bytes")

        # Deserialize
        restored = sdr_oran_pb2.IQSampleBatch()
        restored.ParseFromString(serialized)

        # Verify
        assert restored.station_id == original.station_id
        assert restored.band == original.band
        assert restored.center_frequency_hz == original.center_frequency_hz
        assert restored.snr_db == original.snr_db

        print(f"✅ Deserialized successfully:")
        print(f"   - Station: {restored.station_id}")
        print(f"   - Band: {restored.band}")
        print(f"   - Fc: {restored.center_frequency_hz/1e9:.1f} GHz")
        print(f"   - SNR: {restored.snr_db:.1f} dB")

        print()
        return True

    except Exception as e:
        print(f"❌ Serialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "gRPC Stub Verification Test Suite" + " " * 14 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    tests = [
        ("Import Generated Stubs", test_imports),
        ("Create Protocol Buffer Messages", test_message_creation),
        ("Verify gRPC Service Stub", test_service_stub),
        ("Test Serialization/Deserialization", test_serialization)
    ]

    results = []

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print()
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print()
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print()
        print("🎉 All tests passed! gRPC stubs are working correctly.")
        print()
        print("Next steps:")
        print("   1. Start gRPC server: python sdr_grpc_server.py")
        print("   2. In another terminal, run client: python oran_grpc_client.py")
        print("   3. Or start VITA 49 bridge: python ../vita49-bridge/vita49_receiver.py")
        return 0
    else:
        print()
        print("⚠️  Some tests failed. Please check errors above.")
        print("   Try regenerating stubs: python generate_grpc_stubs.py")
        return 1


if __name__ == '__main__':
    sys.exit(main())
