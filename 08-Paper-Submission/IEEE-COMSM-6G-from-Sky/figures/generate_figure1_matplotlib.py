#!/usr/bin/env python3
"""
Generate Figure 1: System Architecture Diagram using matplotlib
Simplified version when Graphviz is not available
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.lines as mlines

# Set publication quality
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica']
plt.rcParams['font.size'] = 8

# Create figure (7.16 inches wide for two-column)
fig, ax = plt.subplots(figsize=(7.16, 5))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis('off')

# Colors for each layer
color_physical = '#BBDEFB'    # Blue
color_sdr = '#C8E6C9'         # Green
color_oran = '#FFE0B2'        # Orange
color_cloud = '#E1BEE7'       # Purple

# Layer 4: Cloud-Native Orchestration (Top)
layer4_y = 8.5
ax.add_patch(FancyBboxPatch((0.5, layer4_y), 9, 1.2,
                             boxstyle="round,pad=0.05",
                             facecolor=color_cloud, edgecolor='#7B1FA2', linewidth=1.5))
ax.text(5, layer4_y + 0.95, 'Layer 4: Cloud-Native Orchestration',
        ha='center', va='top', fontsize=9, fontweight='bold')
ax.text(2, layer4_y + 0.5, 'Kubernetes\nCluster', ha='center', va='center', fontsize=7)
ax.text(5, layer4_y + 0.5, 'Nephio Network\nAutomation', ha='center', va='center', fontsize=7)
ax.text(8, layer4_y + 0.5, 'Prometheus +\nGrafana', ha='center', va='center', fontsize=7)

# Layer 3: O-RAN Components
layer3_y = 6.3
ax.add_patch(FancyBboxPatch((0.5, layer3_y), 9, 1.8,
                             boxstyle="round,pad=0.05",
                             facecolor=color_oran, edgecolor='#F57C00', linewidth=1.5))
ax.text(5, layer3_y + 1.65, 'Layer 3: O-RAN Components',
        ha='center', va='top', fontsize=9, fontweight='bold')
ax.text(2, layer3_y + 0.9, 'OpenAirInterface\n5G-NTN gNB\n(DU + CU)',
        ha='center', va='center', fontsize=7)
ax.text(5, layer3_y + 0.9, 'Near-RT RIC\nPlatform', ha='center', va='center', fontsize=7)
ax.text(8, layer3_y + 0.9, 'Intelligent xApps\n(Traffic Steering,\nQoS Optimization)',
        ha='center', va='center', fontsize=7)

# E2 interface arrow
arrow1 = FancyArrowPatch((3, layer3_y + 0.9), (4.2, layer3_y + 0.9),
                         arrowstyle='->', mutation_scale=15, linewidth=1.5,
                         color='#F57C00', label='E2')
ax.add_patch(arrow1)
ax.text(3.6, layer3_y + 1.2, 'E2', fontsize=6, color='#F57C00', fontweight='bold')

# Layer 2: SDR Platform
layer2_y = 4.2
ax.add_patch(FancyBboxPatch((0.5, layer2_y), 9, 1.7,
                             boxstyle="round,pad=0.05",
                             facecolor=color_sdr, edgecolor='#388E3C', linewidth=1.5))
ax.text(5, layer2_y + 1.55, 'Layer 2: SDR Platform',
        ha='center', va='top', fontsize=9, fontweight='bold')
ax.text(2.5, layer2_y + 0.85, 'VITA 49.2\nVRT Receiver', ha='center', va='center', fontsize=7)
ax.text(5, layer2_y + 0.85, 'gRPC Bidirectional\nStreaming Server',
        ha='center', va='center', fontsize=7)
ax.text(7.5, layer2_y + 0.85, 'FastAPI\nREST Gateway', ha='center', va='center', fontsize=7)

# Layer 1: Physical Infrastructure (Bottom)
layer1_y = 1.5
ax.add_patch(FancyBboxPatch((0.5, layer1_y), 9, 2.3,
                             boxstyle="round,pad=0.05",
                             facecolor=color_physical, edgecolor='#1976D2', linewidth=1.5))
ax.text(5, layer1_y + 2.15, 'Layer 1: Physical Infrastructure',
        ha='center', va='top', fontsize=9, fontweight='bold')
ax.text(2, layer1_y + 1.15, 'USRP X310\n+ GPSDO', ha='center', va='center', fontsize=7)
ax.text(4, layer1_y + 1.15, 'Multi-band\nAntenna\n(C/Ku/Ka)',
        ha='center', va='center', fontsize=7)
ax.text(6.5, layer1_y + 1.15, '3x Compute\nServers\n(32 cores each)',
        ha='center', va='center', fontsize=7)
ax.text(8.5, layer1_y + 1.15, '10 GbE\nNetworking', ha='center', va='center', fontsize=7)

# Satellite (external, top)
ax.add_patch(mpatches.Ellipse((9.2, 9.7), 0.6, 0.4,
                               facecolor='#FFECB3', edgecolor='#FF6F00',
                               linewidth=1.5, linestyle='--'))
ax.text(9.2, 9.7, 'LEO/MEO/GEO\nSatellite', ha='center', va='center', fontsize=6)

# Inter-layer connections (arrows)
# Physical to SDR
ax.annotate('', xy=(5, layer2_y + 0.1), xytext=(5, layer1_y + 2.2),
            arrowprops=dict(arrowstyle='->', lw=1, color='gray'))
ax.text(5.3, (layer1_y + 2.2 + layer2_y) / 2, 'IQ Stream', fontsize=6, color='gray')

# SDR to O-RAN
ax.annotate('', xy=(5, layer3_y + 0.1), xytext=(5, layer2_y + 1.6),
            arrowprops=dict(arrowstyle='->', lw=1, color='gray'))
ax.text(5.3, (layer2_y + 1.6 + layer3_y) / 2, 'Real-time IQ', fontsize=6, color='gray')

# O-RAN to Cloud
ax.annotate('', xy=(5, layer4_y + 0.1), xytext=(5, layer3_y + 1.7),
            arrowprops=dict(arrowstyle='->', lw=1, color='gray', linestyle='dashed'))
ax.text(5.3, (layer3_y + 1.7 + layer4_y) / 2, 'Deployment', fontsize=6, color='gray')

# Cloud to O-RAN management (A1)
ax.annotate('', xy=(6.5, layer3_y + 1.65), xytext=(6.5, layer4_y + 0.15),
            arrowprops=dict(arrowstyle='->', lw=1.5, color='#7B1FA2'))
ax.text(6.9, (layer3_y + 1.65 + layer4_y) / 2, 'A1 Policy',
        fontsize=6, color='#7B1FA2', fontweight='bold')

# Satellite to Antenna
ax.annotate('', xy=(4, layer1_y + 2.15), xytext=(8.9, 9.5),
            arrowprops=dict(arrowstyle='->', lw=1.5, color='#FF6F00'))
ax.text(6, 6.5, 'RF Link\n(C/Ku/Ka)', fontsize=6, color='#FF6F00', fontweight='bold')

# Legend
legend_x = 0.7
legend_y = 0.5
ax.text(legend_x, legend_y + 0.7, 'Interface Legend:', fontsize=7, fontweight='bold')
ax.text(legend_x, legend_y + 0.45, 'E2: Near-RT RIC Interface', fontsize=6)
ax.text(legend_x, legend_y + 0.25, 'A1: Non-RT RIC Policy', fontsize=6)
ax.text(legend_x, legend_y + 0.05, 'F1: CU-DU Interface', fontsize=6)

ax.text(legend_x + 3, legend_y + 0.45, 'FAPI: PHY-MAC Interface', fontsize=6)
ax.text(legend_x + 3, legend_y + 0.25, 'IQ: In-phase/Quadrature', fontsize=6)
ax.text(legend_x + 3, legend_y + 0.05, 'RF: Radio Frequency', fontsize=6)

# Title
ax.text(5, 0.2, 'Fig. 1. Cloud-Native SDR-O-RAN Platform Architecture for NTN Operations',
        ha='center', va='center', fontsize=8, style='italic')

plt.tight_layout(pad=0.3)

# Save
print("Generating Figure 1: Architecture Diagram...")
plt.savefig('figure1_architecture.pdf', dpi=300, bbox_inches='tight', format='pdf')
print("Saved: figure1_architecture.pdf")
plt.savefig('figure1_architecture.eps', dpi=300, bbox_inches='tight', format='eps')
print("Saved: figure1_architecture.eps")
plt.savefig('figure1_architecture.png', dpi=600, bbox_inches='tight', format='png')
print("Saved: figure1_architecture.png")

print("\nFigure 1 generation complete!")
