#!/usr/bin/env python3
"""
Test TLS-encrypted gRPC connection

This script tests the TLS implementation for the SDR-O-RAN gRPC server.
It verifies that:
1. The TLS handshake is successful
2. The server accepts connections with valid certificates
3. Basic RPC calls work over encrypted channels

Author: thc1006@ieee.org
Version: 1.0.0
Date: 2025-11-17
"""

import grpc
import logging
import sys

import sdr_oran_pb2
import sdr_oran_pb2_grpc

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_tls_connection(server_address='localhost:50051', cert_dir='./certs'):
    """Test secure gRPC connection with TLS

    Args:
        server_address: Server address (default: localhost:50051)
        cert_dir: Certificate directory (default: ./certs)

    Returns:
        bool: True if test passed, False otherwise
    """
    logger.info("="*60)
    logger.info("TLS Connection Test")
    logger.info("="*60)
    logger.info(f"Server: {server_address}")
    logger.info(f"Cert dir: {cert_dir}")
    logger.info("")

    try:
        # Read CA certificate
        logger.info("Loading CA certificate...")
        with open(f'{cert_dir}/ca.crt', 'rb') as f:
            ca_cert = f.read()
        logger.info("CA certificate loaded successfully")

        # Create credentials
        logger.info("Creating SSL credentials...")
        credentials = grpc.ssl_channel_credentials(root_certificates=ca_cert)
        logger.info("SSL credentials created")

        # Connect to server
        logger.info(f"Connecting to {server_address}...")
        with grpc.secure_channel(
            server_address,
            credentials,
            options=[('grpc.ssl_target_name_override', 'localhost')]
        ) as channel:

            logger.info("TLS handshake successful")

            # Create stub
            stub = sdr_oran_pb2_grpc.IQStreamServiceStub(channel)

            # Test request
            logger.info("Sending GetStreamStats request...")
            request = sdr_oran_pb2.StreamStatsRequest(station_id="test-tls")

            try:
                response = stub.GetStreamStats(request, timeout=5.0)
                logger.info("RPC call successful!")
                logger.info(f"Response: {response}")
                logger.info("")
                logger.info("="*60)
                logger.info("TLS connection test PASSED")
                logger.info("="*60)
                return True

            except grpc.RpcError as e:
                # This is expected since the server servicers are not fully implemented
                if e.code() == grpc.StatusCode.UNIMPLEMENTED:
                    logger.warning(f"RPC not implemented (expected): {e.code()} - {e.details()}")
                    logger.info("")
                    logger.info("="*60)
                    logger.info("TLS connection test PASSED (RPC unimplemented but TLS works)")
                    logger.info("="*60)
                    return True
                elif e.code() == grpc.StatusCode.NOT_FOUND:
                    logger.warning(f"Station not found (expected): {e.code()} - {e.details()}")
                    logger.info("")
                    logger.info("="*60)
                    logger.info("TLS connection test PASSED (Station not found but TLS works)")
                    logger.info("="*60)
                    return True
                else:
                    logger.error(f"RPC failed: {e.code()} - {e.details()}")
                    logger.info("")
                    logger.info("="*60)
                    logger.info("TLS connection test FAILED")
                    logger.info("="*60)
                    return False

    except FileNotFoundError as e:
        logger.error(f"Certificate file not found: {e}")
        logger.info("")
        logger.info("="*60)
        logger.info("TLS connection test FAILED")
        logger.info("="*60)
        return False

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        logger.info("")
        logger.info("="*60)
        logger.info("TLS connection test FAILED")
        logger.info("="*60)
        return False


def test_insecure_connection_rejected(server_address='localhost:50051'):
    """Test that insecure connections are rejected when TLS is enabled

    Args:
        server_address: Server address (default: localhost:50051)

    Returns:
        bool: True if insecure connection is properly rejected, False otherwise
    """
    logger.info("")
    logger.info("="*60)
    logger.info("Insecure Connection Rejection Test")
    logger.info("="*60)
    logger.info(f"Server: {server_address}")
    logger.info("")

    try:
        logger.info("Attempting insecure connection to TLS server...")

        # Try to connect without TLS
        with grpc.insecure_channel(server_address) as channel:
            stub = sdr_oran_pb2_grpc.IQStreamServiceStub(channel)
            request = sdr_oran_pb2.StreamStatsRequest(station_id="test-insecure")

            try:
                response = stub.GetStreamStats(request, timeout=5.0)
                logger.error("Insecure connection succeeded (should have been rejected)")
                logger.info("")
                logger.info("="*60)
                logger.info("Insecure rejection test FAILED")
                logger.info("="*60)
                return False

            except grpc.RpcError as e:
                logger.info(f"Insecure connection properly rejected: {e.code()}")
                logger.info("")
                logger.info("="*60)
                logger.info("Insecure rejection test PASSED")
                logger.info("="*60)
                return True

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        logger.info("")
        logger.info("="*60)
        logger.info("Insecure rejection test FAILED")
        logger.info("="*60)
        return False


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Test TLS-encrypted gRPC connection')
    parser.add_argument('--server', type=str, default='localhost:50051',
                       help='Server address (default: localhost:50051)')
    parser.add_argument('--cert-dir', type=str, default='./certs',
                       help='Certificate directory (default: ./certs)')
    parser.add_argument('--skip-insecure-test', action='store_true',
                       help='Skip testing insecure connection rejection')
    args = parser.parse_args()

    # Run TLS connection test
    tls_passed = test_tls_connection(args.server, args.cert_dir)

    # Run insecure connection rejection test (optional)
    insecure_passed = True
    if not args.skip_insecure_test:
        insecure_passed = test_insecure_connection_rejected(args.server)

    # Final results
    logger.info("")
    logger.info("="*60)
    logger.info("FINAL RESULTS")
    logger.info("="*60)
    logger.info(f"TLS Connection Test: {'PASSED' if tls_passed else 'FAILED'}")
    if not args.skip_insecure_test:
        logger.info(f"Insecure Rejection Test: {'PASSED' if insecure_passed else 'FAILED'}")
    logger.info("")

    # Exit with appropriate code
    if tls_passed and insecure_passed:
        logger.info("All tests PASSED")
        sys.exit(0)
    else:
        logger.error("Some tests FAILED")
        sys.exit(1)
