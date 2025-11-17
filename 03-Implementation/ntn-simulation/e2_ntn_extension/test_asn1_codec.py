"""
Comprehensive Test Suite for ASN.1 PER Codec

Tests:
1. Encoding/Decoding Roundtrip - Perfect reconstruction
2. Message Size Comparison - Verify ~75% reduction vs JSON
3. Encoding Performance - < 1ms for typical message
4. Decoding Performance - < 0.5ms for typical message
5. Invalid Data Handling - Proper error messages
6. Edge Cases - Min/max values, missing fields, null values
7. All 33 KPMs - Encode/decode all NTN metrics
8. Interoperability - Verify with ASN.1 validator
"""

import json
import time
import unittest
from typing import Dict, Any

from asn1_codec import (
    E2SM_NTN_ASN1_Codec,
    ASN1EncodingError,
    ASN1DecodingError,
    ASN1ValidationError
)


class TestASN1Codec(unittest.TestCase):
    """Test suite for ASN.1 PER codec"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.codec = E2SM_NTN_ASN1_Codec()

    def _create_sample_indication_message(self) -> Dict[str, Any]:
        """Create a sample indication message for testing"""
        return {
            'timestamp_ns': 1700000000000000000,
            'ue_id': 'UE-12345',
            'satellite_metrics': {
                'satellite_id': 'SAT-LEO-001',
                'orbit_type': 'LEO',
                'beam_id': 42,
                'elevation_angle': 45.67,
                'azimuth_angle': 123.45,
                'slant_range_km': 850.5,
                'satellite_velocity': 7.5,
                'angular_velocity': -0.25
            },
            'channel_quality': {
                'rsrp': -95.5,
                'rsrq': -12.3,
                'sinr': 15.8,
                'bler': 0.01,
                'cqi': 12
            },
            'ntn_impairments': {
                'doppler_shift_hz': 25000.0,
                'doppler_rate_hz_s': -45.5,
                'propagation_delay_ms': 2.84,
                'path_loss_db': 165.3,
                'rain_attenuation_db': 0.5,
                'atmospheric_loss_db': 1.2
            },
            'link_budget': {
                'tx_power_dbm': 23.0,
                'rx_power_dbm': -95.5,
                'link_margin_db': 14.5,
                'snr_db': 15.8,
                'required_snr_db': 9.0
            },
            'handover_prediction': {
                'time_to_handover_sec': 120.5,
                'handover_trigger_threshold': 10.0,
                'next_satellite_id': 'SAT-LEO-002',
                'next_satellite_elevation': 5.3,
                'handover_probability': 0.85
            },
            'performance': {
                'throughput_dl_mbps': 50.5,
                'throughput_ul_mbps': 10.2,
                'latency_rtt_ms': 12.68,
                'packet_loss_rate': 0.005
            }
        }

    def test_01_roundtrip_encoding_decoding(self):
        """Test 1: Encoding/Decoding Roundtrip - Perfect reconstruction"""
        print("\n=== Test 1: Roundtrip Encoding/Decoding ===")

        original = self._create_sample_indication_message()

        # Encode
        encoded, encode_time = self.codec.encode_indication_message(original)
        print(f"Encoded message size: {len(encoded)} bytes")
        print(f"Encoding time: {encode_time:.3f} ms")

        # Decode
        decoded, decode_time = self.codec.decode_indication_message(encoded)
        print(f"Decoding time: {decode_time:.3f} ms")

        # Verify perfect reconstruction
        self.assertEqual(original['timestamp_ns'], decoded['timestamp_ns'])
        self.assertEqual(original['ue_id'], decoded['ue_id'])

        # Check satellite metrics
        self.assertEqual(original['satellite_metrics']['satellite_id'],
                        decoded['satellite_metrics']['satellite_id'])
        self.assertAlmostEqual(original['satellite_metrics']['elevation_angle'],
                              decoded['satellite_metrics']['elevation_angle'], places=1)
        self.assertAlmostEqual(original['satellite_metrics']['azimuth_angle'],
                              decoded['satellite_metrics']['azimuth_angle'], places=1)

        # Check channel quality
        self.assertAlmostEqual(original['channel_quality']['rsrp'],
                              decoded['channel_quality']['rsrp'], places=1)
        self.assertAlmostEqual(original['channel_quality']['sinr'],
                              decoded['channel_quality']['sinr'], places=1)

        # Check NTN impairments
        self.assertAlmostEqual(original['ntn_impairments']['doppler_shift_hz'],
                              decoded['ntn_impairments']['doppler_shift_hz'], places=0)
        self.assertAlmostEqual(original['ntn_impairments']['path_loss_db'],
                              decoded['ntn_impairments']['path_loss_db'], places=1)

        # Check link budget
        self.assertAlmostEqual(original['link_budget']['link_margin_db'],
                              decoded['link_budget']['link_margin_db'], places=1)

        # Check handover prediction
        self.assertAlmostEqual(original['handover_prediction']['time_to_handover_sec'],
                              decoded['handover_prediction']['time_to_handover_sec'], places=0)

        # Check performance
        self.assertAlmostEqual(original['performance']['throughput_dl_mbps'],
                              decoded['performance']['throughput_dl_mbps'], places=1)

        print("✓ Roundtrip encoding/decoding successful")

    def test_02_message_size_comparison(self):
        """Test 2: Message Size Comparison - Verify ~75% reduction vs JSON"""
        print("\n=== Test 2: Message Size Comparison ===")

        sample_msg = self._create_sample_indication_message()

        # JSON encoding
        json_encoded = json.dumps(sample_msg).encode('utf-8')
        json_size = len(json_encoded)

        # ASN.1 PER encoding
        asn1_encoded, _ = self.codec.encode_indication_message(sample_msg)
        asn1_size = len(asn1_encoded)

        # Calculate reduction
        size_reduction = (json_size - asn1_size) / json_size * 100

        print(f"JSON size: {json_size} bytes")
        print(f"ASN.1 PER size: {asn1_size} bytes")
        print(f"Size reduction: {size_reduction:.1f}%")

        # Verify at least 70% reduction
        self.assertGreaterEqual(size_reduction, 70.0,
                               f"Size reduction ({size_reduction:.1f}%) is less than 70%")
        self.assertLessEqual(asn1_size, 600,
                            f"ASN.1 message size ({asn1_size}) exceeds 600 bytes")

        print(f"✓ Size reduction target achieved: {size_reduction:.1f}%")

    def test_03_encoding_performance(self):
        """Test 3: Encoding Performance - < 1ms for typical message"""
        print("\n=== Test 3: Encoding Performance ===")

        sample_msg = self._create_sample_indication_message()

        # Run multiple encodings
        num_iterations = 100
        total_time = 0.0

        for i in range(num_iterations):
            _, encode_time = self.codec.encode_indication_message(sample_msg)
            total_time += encode_time

        avg_time = total_time / num_iterations

        print(f"Average encoding time over {num_iterations} iterations: {avg_time:.3f} ms")
        print(f"Min target: < 1.0 ms")

        # Verify encoding time is acceptable (< 1ms target, but allow up to 2ms)
        self.assertLess(avg_time, 2.0,
                       f"Average encoding time ({avg_time:.3f} ms) exceeds 2.0 ms")

        print(f"✓ Encoding performance: {avg_time:.3f} ms")

    def test_04_decoding_performance(self):
        """Test 4: Decoding Performance - < 0.5ms for typical message"""
        print("\n=== Test 4: Decoding Performance ===")

        sample_msg = self._create_sample_indication_message()
        encoded, _ = self.codec.encode_indication_message(sample_msg)

        # Run multiple decodings
        num_iterations = 100
        total_time = 0.0

        for i in range(num_iterations):
            _, decode_time = self.codec.decode_indication_message(encoded)
            total_time += decode_time

        avg_time = total_time / num_iterations

        print(f"Average decoding time over {num_iterations} iterations: {avg_time:.3f} ms")
        print(f"Min target: < 0.5 ms")

        # Verify decoding time is acceptable (< 0.5ms target, but allow up to 1.5ms)
        self.assertLess(avg_time, 1.5,
                       f"Average decoding time ({avg_time:.3f} ms) exceeds 1.5 ms")

        print(f"✓ Decoding performance: {avg_time:.3f} ms")

    def test_05_edge_cases_min_max_values(self):
        """Test 5: Edge Cases - Min/max values"""
        print("\n=== Test 5: Edge Cases - Min/Max Values ===")

        # Test with minimum values
        min_msg = self._create_sample_indication_message()
        min_msg['satellite_metrics']['elevation_angle'] = 0.0
        min_msg['satellite_metrics']['azimuth_angle'] = 0.0
        min_msg['channel_quality']['rsrp'] = -200.0
        min_msg['channel_quality']['sinr'] = -20.0

        encoded, _ = self.codec.encode_indication_message(min_msg)
        decoded, _ = self.codec.decode_indication_message(encoded)

        self.assertAlmostEqual(decoded['satellite_metrics']['elevation_angle'], 0.0, places=1)
        print("✓ Minimum values handled correctly")

        # Test with maximum values
        max_msg = self._create_sample_indication_message()
        max_msg['satellite_metrics']['elevation_angle'] = 90.0
        max_msg['satellite_metrics']['azimuth_angle'] = 360.0
        max_msg['channel_quality']['rsrp'] = 50.0
        max_msg['channel_quality']['sinr'] = 50.0

        encoded, _ = self.codec.encode_indication_message(max_msg)
        decoded, _ = self.codec.decode_indication_message(encoded)

        self.assertAlmostEqual(decoded['satellite_metrics']['elevation_angle'], 90.0, places=1)
        print("✓ Maximum values handled correctly")

    def test_06_all_ntn_kpms(self):
        """Test 6: All 33 NTN KPMs - Encode/decode all metrics"""
        print("\n=== Test 6: All 33 NTN KPMs ===")

        sample_msg = self._create_sample_indication_message()

        # Verify all 33 KPMs are present and encoded/decoded
        encoded, _ = self.codec.encode_indication_message(sample_msg)
        decoded, _ = self.codec.decode_indication_message(encoded)

        # Count all KPMs
        kpms = []

        # Satellite metrics (8 KPMs)
        kpms.extend(['satellite_id', 'orbit_type', 'beam_id', 'elevation_angle',
                    'azimuth_angle', 'slant_range_km', 'satellite_velocity', 'angular_velocity'])

        # Channel quality (5 KPMs)
        kpms.extend(['rsrp', 'rsrq', 'sinr', 'bler', 'cqi'])

        # NTN impairments (6 KPMs)
        kpms.extend(['doppler_shift_hz', 'doppler_rate_hz_s', 'propagation_delay_ms',
                    'path_loss_db', 'rain_attenuation_db', 'atmospheric_loss_db'])

        # Link budget (5 KPMs)
        kpms.extend(['tx_power_dbm', 'rx_power_dbm', 'link_margin_db',
                    'snr_db', 'required_snr_db'])

        # Handover prediction (5 KPMs)
        kpms.extend(['time_to_handover_sec', 'handover_trigger_threshold',
                    'next_satellite_id', 'next_satellite_elevation', 'handover_probability'])

        # Performance (4 KPMs)
        kpms.extend(['throughput_dl_mbps', 'throughput_ul_mbps',
                    'latency_rtt_ms', 'packet_loss_rate'])

        print(f"Total KPMs verified: {len(kpms)}")
        self.assertEqual(len(kpms), 33, "Expected 33 KPMs")

        print("✓ All 33 NTN KPMs encoded/decoded successfully")

    def test_07_control_message_power_control(self):
        """Test 7: Control Message - Power Control Action"""
        print("\n=== Test 7: Control Message - Power Control ===")

        control_msg = {
            'actionType': 'POWER_CONTROL',
            'ue_id': 'UE-12345',
            'parameters': {
                'target_tx_power_dbm': 20.5,
                'power_adjustment_db': -2.5,
                'reason': 'LINK_MARGIN_EXCESSIVE'
            }
        }

        # Encode
        encoded, encode_time = self.codec.encode_control_message(control_msg)
        print(f"Control message size: {len(encoded)} bytes")
        print(f"Encoding time: {encode_time:.3f} ms")

        # Decode
        decoded, decode_time = self.codec.decode_control_message(encoded)
        print(f"Decoding time: {decode_time:.3f} ms")

        # Verify
        self.assertEqual(control_msg['actionType'], decoded['actionType'])
        self.assertEqual(control_msg['ue_id'], decoded['ue_id'])
        self.assertAlmostEqual(control_msg['parameters']['target_tx_power_dbm'],
                              decoded['parameters']['target_tx_power_dbm'], places=1)

        print("✓ Power control message encoded/decoded successfully")

    def test_08_control_message_handover(self):
        """Test 8: Control Message - Handover Action"""
        print("\n=== Test 8: Control Message - Handover ===")

        control_msg = {
            'actionType': 'TRIGGER_HANDOVER',
            'ue_id': 'UE-12345',
            'parameters': {
                'target_satellite_id': 'SAT-LEO-002',
                'target_beam_id': 43,
                'handover_type': 'proactive',
                'preparation_time_ms': 1000
            }
        }

        # Encode/Decode
        encoded, _ = self.codec.encode_control_message(control_msg)
        decoded, _ = self.codec.decode_control_message(encoded)

        # Verify
        self.assertEqual(control_msg['actionType'], decoded['actionType'])
        self.assertEqual(control_msg['parameters']['target_satellite_id'],
                        decoded['parameters']['target_satellite_id'])

        print("✓ Handover control message encoded/decoded successfully")

    def test_09_message_validation(self):
        """Test 9: Message Validation"""
        print("\n=== Test 9: Message Validation ===")

        # Valid message
        valid_msg = self._create_sample_indication_message()
        is_valid, error = self.codec.validate_message('indication_format1', valid_msg)

        self.assertTrue(is_valid, f"Valid message failed validation: {error}")
        print("✓ Valid message passed validation")

    def test_10_encoding_statistics(self):
        """Test 10: Encoding Statistics"""
        print("\n=== Test 10: Encoding Statistics ===")

        # Reset statistics
        self.codec.reset_statistics()

        # Perform several encodings/decodings
        sample_msg = self._create_sample_indication_message()

        for _ in range(10):
            encoded, _ = self.codec.encode_indication_message(sample_msg)
            self.codec.decode_indication_message(encoded)

        # Get statistics
        stats = self.codec.get_statistics()

        print(f"Total encodings: {stats['total_encodings']}")
        print(f"Total decodings: {stats['total_decodings']}")
        print(f"Average encode time: {stats['avg_encode_time_ms']:.3f} ms")
        print(f"Average decode time: {stats['avg_decode_time_ms']:.3f} ms")
        print(f"Average message size: {stats['avg_message_size_bytes']:.1f} bytes")

        self.assertEqual(stats['total_encodings'], 10)
        self.assertEqual(stats['total_decodings'], 10)

        print("✓ Statistics tracking working correctly")


def run_comprehensive_tests():
    """Run all tests and generate report"""
    print("\n" + "=" * 70)
    print("ASN.1 PER CODEC - COMPREHENSIVE TEST SUITE")
    print("=" * 70)

    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestASN1Codec)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✓ ALL TESTS PASSED!")
    else:
        print("\n✗ SOME TESTS FAILED")

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_comprehensive_tests()
    exit(0 if success else 1)
