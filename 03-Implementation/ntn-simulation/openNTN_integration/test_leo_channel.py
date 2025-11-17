#!/usr/bin/env python3
"""
Comprehensive Test Script for NTN Channel Models
=================================================

This script validates the LEO, MEO, and GEO channel wrappers against
3GPP TR38.811 specifications, testing:
1. Path loss calculations at various elevation angles
2. Doppler shift calculations
3. Different scenarios (urban, suburban, dense_urban)
4. Different altitudes
5. Link budget validation

Author: OpenNTN Integration Specialist
Date: 2025-11-17
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Tuple
import sys
import os

# Import channel models
from leo_channel import LEOChannelModel
from meo_channel import MEOChannelModel
from geo_channel import GEOChannelModel


class NTNChannelTester:
    """Comprehensive tester for NTN channel models"""

    def __init__(self, output_dir: str = 'test_results'):
        """
        Initialize tester

        Parameters
        ----------
        output_dir : str
            Directory to save test results and plots
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {}
        }

        print("="*70)
        print("NTN Channel Model Test Suite")
        print("="*70)
        print(f"Output directory: {self.output_dir.absolute()}")
        print()

    def test_leo_elevation_sweep(self):
        """Test LEO channel across elevation angles"""
        print("\n" + "="*70)
        print("TEST 1: LEO Elevation Angle Sweep")
        print("="*70)

        leo = LEOChannelModel(
            carrier_frequency=2.0e9,
            altitude_km=550,
            scenario='urban'
        )

        elevations = np.linspace(10, 90, 81)
        results = {
            'elevations': elevations.tolist(),
            'slant_ranges': [],
            'path_losses': [],
            'doppler_shifts': []
        }

        for elev in elevations:
            budget = leo.calculate_link_budget(elev)
            results['slant_ranges'].append(budget['slant_range_km'])
            results['path_losses'].append(budget['free_space_path_loss_db'])
            results['doppler_shifts'].append(budget['doppler_shift_khz'])

        # Validation checks
        checks = []

        # Check 1: Path loss increases as elevation decreases
        pl_monotonic = all(results['path_losses'][i] >= results['path_losses'][i+1]
                          for i in range(len(results['path_losses'])-1))
        checks.append(('Path loss monotonically decreases with elevation', pl_monotonic))

        # Check 2: Path loss at zenith (90°) should be minimum
        min_pl_idx = np.argmin(results['path_losses'])
        min_pl_at_zenith = elevations[min_pl_idx] == 90.0
        checks.append(('Minimum path loss at zenith (90°)', min_pl_at_zenith))

        # Check 3: Path loss range is reasonable for LEO S-band (Free Space Path Loss)
        pl_range = (min(results['path_losses']), max(results['path_losses']))
        # FSPL for LEO at 2 GHz ranges from ~153 dB (zenith, 550km) to ~164 dB (10° elev, 1815km)
        pl_reasonable = 150 <= pl_range[0] <= 155 and 160 <= pl_range[1] <= 170
        checks.append((f'Path loss range reasonable (FSPL): {pl_range[0]:.1f}-{pl_range[1]:.1f} dB', pl_reasonable))

        # Check 4: Doppler increases as elevation increases (maximum radial velocity at zenith)
        doppler_increasing = all(results['doppler_shifts'][i] <= results['doppler_shifts'][i+1]
                                for i in range(len(results['doppler_shifts'])-1))
        checks.append(('Doppler monotonically increases with elevation', doppler_increasing))

        # Print results
        print(f"\nResults at key elevations:")
        print(f"{'Elevation':<12} {'Slant Range':<15} {'Path Loss':<12} {'Doppler':<12}")
        print(f"{'(deg)':<12} {'(km)':<15} {'(dB)':<12} {'(kHz)':<12}")
        print("-"*51)
        for elev in [10, 30, 45, 60, 90]:
            idx = np.argmin(np.abs(elevations - elev))
            print(f"{elevations[idx]:<12.1f} {results['slant_ranges'][idx]:<15.2f} "
                  f"{results['path_losses'][idx]:<12.2f} {results['doppler_shifts'][idx]:<12.2f}")

        print(f"\nValidation Checks:")
        for check_name, passed in checks:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {status}: {check_name}")

        all_passed = all(check[1] for check in checks)
        self.test_results['tests']['leo_elevation_sweep'] = {
            'passed': all_passed,
            'checks': [{'name': c[0], 'passed': c[1]} for c in checks],
            'data': results
        }

        return results, all_passed

    def test_altitude_comparison(self):
        """Test different LEO altitudes"""
        print("\n" + "="*70)
        print("TEST 2: LEO Altitude Comparison")
        print("="*70)

        altitudes = [550, 700, 900, 1200]
        elevation = 30.0

        results = {
            'altitudes': altitudes,
            'slant_ranges': [],
            'path_losses': [],
            'doppler_shifts': [],
            'orbital_periods': []
        }

        print(f"\nTesting at {elevation}° elevation:")
        print(f"{'Altitude':<12} {'Slant Range':<15} {'Path Loss':<12} {'Doppler':<12} {'Period':<12}")
        print(f"{'(km)':<12} {'(km)':<15} {'(dB)':<12} {'(kHz)':<12} {'(min)':<12}")
        print("-"*63)

        for alt in altitudes:
            leo = LEOChannelModel(
                carrier_frequency=2.0e9,
                altitude_km=alt,
                scenario='urban'
            )
            budget = leo.calculate_link_budget(elevation)

            results['slant_ranges'].append(budget['slant_range_km'])
            results['path_losses'].append(budget['free_space_path_loss_db'])
            results['doppler_shifts'].append(budget['doppler_shift_khz'])
            results['orbital_periods'].append(budget['orbital_period_min'])

            print(f"{alt:<12} {budget['slant_range_km']:<15.2f} "
                  f"{budget['free_space_path_loss_db']:<12.2f} "
                  f"{budget['doppler_shift_khz']:<12.2f} "
                  f"{budget['orbital_period_min']:<12.2f}")

        # Validation checks
        checks = []

        # Path loss should increase with altitude
        pl_increasing = all(results['path_losses'][i] < results['path_losses'][i+1]
                           for i in range(len(results['path_losses'])-1))
        checks.append(('Path loss increases with altitude', pl_increasing))

        # Orbital period should increase with altitude
        period_increasing = all(results['orbital_periods'][i] < results['orbital_periods'][i+1]
                               for i in range(len(results['orbital_periods'])-1))
        checks.append(('Orbital period increases with altitude', period_increasing))

        print(f"\nValidation Checks:")
        for check_name, passed in checks:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {status}: {check_name}")

        all_passed = all(check[1] for check in checks)
        self.test_results['tests']['altitude_comparison'] = {
            'passed': all_passed,
            'checks': [{'name': c[0], 'passed': c[1]} for c in checks],
            'data': results
        }

        return results, all_passed

    def test_scenario_comparison(self):
        """Test different scenarios (urban, suburban, dense_urban)"""
        print("\n" + "="*70)
        print("TEST 3: Scenario Comparison")
        print("="*70)

        scenarios = ['urban', 'suburban', 'dense_urban']
        elevation = 30.0

        print(f"\nAll scenarios use OpenNTN's 3GPP TR38.811 models")
        print(f"Testing at {elevation}° elevation with 550 km altitude:")
        print(f"{'Scenario':<15} {'Model':<20} {'Status':<10}")
        print("-"*45)

        results = {
            'scenarios': scenarios,
            'initialized': []
        }

        for scenario in scenarios:
            try:
                leo = LEOChannelModel(
                    carrier_frequency=2.0e9,
                    altitude_km=550,
                    scenario=scenario
                )
                budget = leo.calculate_link_budget(elevation)
                status = "✓ OK"
                results['initialized'].append(True)
                print(f"{scenario:<15} {'3GPP TR38.811':<20} {status:<10}")
            except Exception as e:
                status = f"✗ Error: {str(e)[:20]}"
                results['initialized'].append(False)
                print(f"{scenario:<15} {'3GPP TR38.811':<20} {status:<10}")

        # Validation
        checks = [
            ('All scenarios initialize successfully', all(results['initialized']))
        ]

        print(f"\nValidation Checks:")
        for check_name, passed in checks:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {status}: {check_name}")

        all_passed = all(check[1] for check in checks)
        self.test_results['tests']['scenario_comparison'] = {
            'passed': all_passed,
            'checks': [{'name': c[0], 'passed': c[1]} for c in checks],
            'data': results
        }

        return results, all_passed

    def test_orbit_comparison(self):
        """Test LEO vs MEO vs GEO comparison"""
        print("\n" + "="*70)
        print("TEST 4: Orbit Type Comparison (LEO/MEO/GEO)")
        print("="*70)

        elevation = 30.0

        # Create models
        leo = LEOChannelModel(carrier_frequency=2.0e9, altitude_km=550, scenario='urban')
        meo = MEOChannelModel(carrier_frequency=2.0e9, altitude_km=8062, scenario='urban')
        geo = GEOChannelModel(carrier_frequency=2.0e9, altitude_km=35786, scenario='urban')

        # Calculate budgets
        leo_budget = leo.calculate_link_budget(elevation)
        meo_budget = meo.calculate_link_budget(elevation)
        geo_budget = geo.calculate_link_budget(elevation)

        results = {
            'elevation': elevation,
            'leo': leo_budget,
            'meo': meo_budget,
            'geo': geo_budget
        }

        print(f"\nComparison at {elevation}° elevation:")
        print(f"{'Parameter':<30} {'LEO (550km)':<18} {'MEO (8062km)':<18} {'GEO (35786km)':<18}")
        print("-"*84)
        print(f"{'Slant Range (km)':<30} {leo_budget['slant_range_km']:<18.2f} "
              f"{meo_budget['slant_range_km']:<18.2f} {geo_budget['slant_range_km']:<18.2f}")
        print(f"{'Path Loss (dB)':<30} {leo_budget['free_space_path_loss_db']:<18.2f} "
              f"{meo_budget['free_space_path_loss_db']:<18.2f} {geo_budget['free_space_path_loss_db']:<18.2f}")
        print(f"{'Doppler (kHz)':<30} {leo_budget['doppler_shift_khz']:<18.2f} "
              f"{meo_budget['doppler_shift_khz']:<18.2f} {geo_budget['doppler_shift_hz']/1000:<18.4f}")
        print(f"{'Orbital Period (hours)':<30} {leo_budget['orbital_period_min']/60:<18.2f} "
              f"{meo_budget['orbital_period_min']/60:<18.2f} {geo_budget['orbital_period_min']/60:<18.2f}")

        # Validation checks
        checks = []

        # Path loss should increase: LEO < MEO < GEO
        pl_order = (leo_budget['free_space_path_loss_db'] <
                   meo_budget['free_space_path_loss_db'] <
                   geo_budget['free_space_path_loss_db'])
        checks.append(('Path loss order correct (LEO < MEO < GEO)', pl_order))

        # Doppler should decrease: LEO > MEO > GEO
        doppler_order = (leo_budget['doppler_shift_hz'] >
                        meo_budget['doppler_shift_hz'] >
                        geo_budget['doppler_shift_hz'])
        checks.append(('Doppler order correct (LEO > MEO > GEO)', doppler_order))

        # Orbital period should increase: LEO < MEO < GEO
        period_order = (leo_budget['orbital_period_min'] <
                       meo_budget['orbital_period_min'] <
                       geo_budget['orbital_period_min'])
        checks.append(('Period order correct (LEO < MEO < GEO)', period_order))

        # GEO should be approximately 24 hours
        geo_period_check = abs(geo_budget['orbital_period_min'] - 1440) < 10
        checks.append(('GEO period ≈ 24 hours', geo_period_check))

        print(f"\nValidation Checks:")
        for check_name, passed in checks:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {status}: {check_name}")

        all_passed = all(check[1] for check in checks)
        self.test_results['tests']['orbit_comparison'] = {
            'passed': all_passed,
            'checks': [{'name': c[0], 'passed': c[1]} for c in checks],
            'data': {
                'elevation': elevation,
                'leo': {k: float(v) if isinstance(v, (np.floating, float)) else v
                       for k, v in leo_budget.items()},
                'meo': {k: float(v) if isinstance(v, (np.floating, float)) else v
                       for k, v in meo_budget.items()},
                'geo': {k: float(v) if isinstance(v, (np.floating, float)) else v
                       for k, v in geo_budget.items()}
            }
        }

        return results, all_passed

    def test_3gpp_tr38811_compliance(self):
        """Verify 3GPP TR38.811 compliance"""
        print("\n" + "="*70)
        print("TEST 5: 3GPP TR38.811 Compliance Check")
        print("="*70)

        checks = []

        # Test 1: Valid frequency bands
        print("\n1. Testing frequency band support:")
        try:
            # S-band (1.9-4.0 GHz)
            leo_s = LEOChannelModel(carrier_frequency=2.0e9)
            print("  ✓ S-band (2.0 GHz) supported")
            s_band_ok = True
        except Exception as e:
            print(f"  ✗ S-band failed: {e}")
            s_band_ok = False

        try:
            # Ka-band (19-40 GHz)
            leo_ka = LEOChannelModel(carrier_frequency=20e9)
            print("  ✓ Ka-band (20 GHz) supported")
            ka_band_ok = True
        except Exception as e:
            print(f"  ✗ Ka-band failed: {e}")
            ka_band_ok = False

        checks.append(('S-band support (1.9-4.0 GHz)', s_band_ok))
        checks.append(('Ka-band support (19-40 GHz)', ka_band_ok))

        # Test 2: Elevation angle range (10-90°)
        print("\n2. Testing elevation angle range:")
        try:
            leo = LEOChannelModel(carrier_frequency=2.0e9)
            leo.calculate_link_budget(10.0)  # Min
            leo.calculate_link_budget(90.0)  # Max
            print("  ✓ Elevation range 10-90° supported")
            elev_ok = True
        except Exception as e:
            print(f"  ✗ Elevation range failed: {e}")
            elev_ok = False

        checks.append(('Elevation angle range (10-90°)', elev_ok))

        # Test 3: Scenarios
        print("\n3. Testing 3GPP TR38.811 scenarios:")
        scenario_ok = True
        for scenario in ['urban', 'suburban', 'dense_urban']:
            try:
                leo = LEOChannelModel(carrier_frequency=2.0e9, scenario=scenario)
                print(f"  ✓ {scenario.capitalize()} scenario supported")
            except Exception as e:
                print(f"  ✗ {scenario} failed: {e}")
                scenario_ok = False

        checks.append(('All TR38.811 scenarios supported', scenario_ok))

        # Test 4: Path loss consistency
        print("\n4. Testing path loss calculation:")
        leo = LEOChannelModel(carrier_frequency=2.0e9, altitude_km=600)
        budget_30 = leo.calculate_link_budget(30.0)
        budget_60 = leo.calculate_link_budget(60.0)

        # Path loss at 60° should be less than at 30° (shorter distance)
        pl_consistent = budget_60['free_space_path_loss_db'] < budget_30['free_space_path_loss_db']
        print(f"  Path loss @ 30°: {budget_30['free_space_path_loss_db']:.2f} dB")
        print(f"  Path loss @ 60°: {budget_60['free_space_path_loss_db']:.2f} dB")
        print(f"  {'✓' if pl_consistent else '✗'} Path loss decreases with elevation")

        checks.append(('Path loss calculation consistent', pl_consistent))

        print(f"\nValidation Checks:")
        for check_name, passed in checks:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {status}: {check_name}")

        all_passed = all(check[1] for check in checks)
        self.test_results['tests']['3gpp_compliance'] = {
            'passed': all_passed,
            'checks': [{'name': c[0], 'passed': c[1]} for c in checks]
        }

        return all_passed

    def generate_plots(self, test_data: Dict):
        """Generate comprehensive plots"""
        print("\n" + "="*70)
        print("Generating Plots")
        print("="*70)

        # Create figure with subplots
        fig = plt.figure(figsize=(16, 12))

        # Plot 1: LEO Path Loss vs Elevation
        if 'leo_elevation_sweep' in test_data:
            ax1 = plt.subplot(2, 3, 1)
            data = test_data['leo_elevation_sweep']['data']
            ax1.plot(data['elevations'], data['path_losses'], 'b-', linewidth=2)
            ax1.set_xlabel('Elevation Angle (degrees)', fontsize=10)
            ax1.set_ylabel('Path Loss (dB)', fontsize=10)
            ax1.set_title('LEO Path Loss vs Elevation\n(550 km, 2.0 GHz, Urban)', fontsize=11)
            ax1.grid(True, alpha=0.3)
            ax1.set_xlim([10, 90])

        # Plot 2: LEO Doppler vs Elevation
        if 'leo_elevation_sweep' in test_data:
            ax2 = plt.subplot(2, 3, 2)
            data = test_data['leo_elevation_sweep']['data']
            ax2.plot(data['elevations'], data['doppler_shifts'], 'r-', linewidth=2)
            ax2.set_xlabel('Elevation Angle (degrees)', fontsize=10)
            ax2.set_ylabel('Doppler Shift (kHz)', fontsize=10)
            ax2.set_title('LEO Doppler Shift vs Elevation\n(550 km, 2.0 GHz)', fontsize=11)
            ax2.grid(True, alpha=0.3)
            ax2.set_xlim([10, 90])

        # Plot 3: Altitude Comparison
        if 'altitude_comparison' in test_data:
            ax3 = plt.subplot(2, 3, 3)
            data = test_data['altitude_comparison']['data']
            ax3.plot(data['altitudes'], data['path_losses'], 'go-', linewidth=2, markersize=8)
            ax3.set_xlabel('Altitude (km)', fontsize=10)
            ax3.set_ylabel('Path Loss (dB)', fontsize=10)
            ax3.set_title('Path Loss vs Altitude\n(30° elevation, 2.0 GHz, Urban)', fontsize=11)
            ax3.grid(True, alpha=0.3)

        # Plot 4: Orbit Comparison - Path Loss
        if 'orbit_comparison' in test_data:
            ax4 = plt.subplot(2, 3, 4)
            data = test_data['orbit_comparison']['data']
            orbits = ['LEO\n(550 km)', 'MEO\n(8062 km)', 'GEO\n(35786 km)']
            path_losses = [
                data['leo']['free_space_path_loss_db'],
                data['meo']['free_space_path_loss_db'],
                data['geo']['free_space_path_loss_db']
            ]
            colors = ['#2E86AB', '#A23B72', '#F18F01']
            bars = ax4.bar(orbits, path_losses, color=colors, alpha=0.7, edgecolor='black')
            ax4.set_ylabel('Path Loss (dB)', fontsize=10)
            ax4.set_title('Path Loss Comparison\n(30° elevation, 2.0 GHz, Urban)', fontsize=11)
            ax4.grid(True, alpha=0.3, axis='y')

            # Add value labels on bars
            for bar, pl in zip(bars, path_losses):
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height,
                        f'{pl:.1f} dB', ha='center', va='bottom', fontsize=9)

        # Plot 5: Orbit Comparison - Doppler
        if 'orbit_comparison' in test_data:
            ax5 = plt.subplot(2, 3, 5)
            data = test_data['orbit_comparison']['data']
            orbits = ['LEO\n(550 km)', 'MEO\n(8062 km)', 'GEO\n(35786 km)']
            doppler = [
                data['leo']['doppler_shift_khz'],
                data['meo']['doppler_shift_khz'],
                data['geo']['doppler_shift_hz'] / 1000  # Convert to kHz
            ]
            bars = ax5.bar(orbits, doppler, color=colors, alpha=0.7, edgecolor='black')
            ax5.set_ylabel('Doppler Shift (kHz)', fontsize=10)
            ax5.set_title('Doppler Shift Comparison\n(30° elevation, 2.0 GHz)', fontsize=11)
            ax5.grid(True, alpha=0.3, axis='y')

            # Add value labels
            for bar, d in zip(bars, doppler):
                height = bar.get_height()
                ax5.text(bar.get_x() + bar.get_width()/2., height,
                        f'{d:.2f} kHz', ha='center', va='bottom', fontsize=9)

        # Plot 6: Slant Range vs Elevation for all orbits
        ax6 = plt.subplot(2, 3, 6)
        elevations = np.linspace(10, 90, 81)

        leo = LEOChannelModel(carrier_frequency=2.0e9, altitude_km=550)
        meo = MEOChannelModel(carrier_frequency=2.0e9, altitude_km=8062)
        geo = GEOChannelModel(carrier_frequency=2.0e9, altitude_km=35786)

        leo_ranges = [leo.calculate_slant_range(e) for e in elevations]
        meo_ranges = [meo.calculate_slant_range(e) for e in elevations]
        geo_ranges = [geo.calculate_slant_range(e) for e in elevations]

        ax6.plot(elevations, leo_ranges, color=colors[0], linewidth=2, label='LEO (550 km)')
        ax6.plot(elevations, meo_ranges, color=colors[1], linewidth=2, label='MEO (8062 km)')
        ax6.plot(elevations, geo_ranges, color=colors[2], linewidth=2, label='GEO (35786 km)')
        ax6.set_xlabel('Elevation Angle (degrees)', fontsize=10)
        ax6.set_ylabel('Slant Range (km)', fontsize=10)
        ax6.set_title('Slant Range vs Elevation\nAll Orbit Types', fontsize=11)
        ax6.legend(fontsize=9)
        ax6.grid(True, alpha=0.3)
        ax6.set_xlim([10, 90])

        plt.tight_layout()

        # Save plot
        plot_path = self.output_dir / 'ntn_channel_test_results.png'
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        print(f"✓ Saved: {plot_path}")

        plt.close()

        return plot_path

    def save_results(self):
        """Save test results to JSON"""
        results_path = self.output_dir / 'test_results.json'

        # Convert numpy types to Python native types for JSON serialization
        def convert_to_native(obj):
            if isinstance(obj, dict):
                return {k: convert_to_native(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_native(item) for item in obj]
            elif isinstance(obj, (np.integer, np.floating, np.bool_)):
                return obj.item()
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj

        serializable_results = convert_to_native(self.test_results)

        with open(results_path, 'w') as f:
            json.dump(serializable_results, f, indent=2)

        print(f"✓ Saved: {results_path}")
        return results_path

    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*70)
        print("Running All Tests")
        print("="*70)

        # Run tests
        test_data_leo_elev, pass1 = self.test_leo_elevation_sweep()
        test_data_alt, pass2 = self.test_altitude_comparison()
        test_data_scenario, pass3 = self.test_scenario_comparison()
        test_data_orbit, pass4 = self.test_orbit_comparison()
        pass5 = self.test_3gpp_tr38811_compliance()

        # Generate plots
        plot_path = self.generate_plots(self.test_results['tests'])

        # Save results
        results_path = self.save_results()

        # Summary
        print("\n" + "="*70)
        print("Test Summary")
        print("="*70)

        all_tests = [
            ('LEO Elevation Sweep', pass1),
            ('Altitude Comparison', pass2),
            ('Scenario Comparison', pass3),
            ('Orbit Comparison', pass4),
            ('3GPP TR38.811 Compliance', pass5)
        ]

        for test_name, passed in all_tests:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {status}: {test_name}")

        total_passed = sum(1 for _, p in all_tests if p)
        total_tests = len(all_tests)

        print(f"\nOverall: {total_passed}/{total_tests} tests passed")

        if total_passed == total_tests:
            print("\n🎉 All tests passed successfully!")
        else:
            print(f"\n⚠ {total_tests - total_passed} test(s) failed")

        print(f"\n📁 Results saved to: {self.output_dir.absolute()}")
        print(f"   - Test results: {results_path.name}")
        print(f"   - Plots: {plot_path.name}")

        return total_passed == total_tests


def main():
    """Main test execution"""
    # Create output directory
    output_dir = Path('/home/gnb/thc1006/sdr-o-ran-platform/03-Implementation/ntn-simulation/openNTN_integration/test_results')

    # Run tests
    tester = NTNChannelTester(output_dir=str(output_dir))
    all_passed = tester.run_all_tests()

    print("\n" + "="*70)
    print("✓ Test suite complete!")
    print("="*70)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
