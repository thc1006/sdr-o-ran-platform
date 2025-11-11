#!/usr/bin/env python3
"""
Generate Figure 2: Throughput Performance vs. Satellite Elevation Angle
IEEE Communications Standards Magazine - Publication Quality

Requirements:
    pip install matplotlib numpy

Output:
    - figure2_performance.pdf (vector format)
    - figure2_performance.eps (vector format)
    - figure2_performance.png (high-resolution raster)
"""

import matplotlib.pyplot as plt
import numpy as np
import os

# Set publication-quality parameters
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica']
plt.rcParams['font.size'] = 9
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['grid.linewidth'] = 0.5
plt.rcParams['lines.linewidth'] = 1.5

# Data from performance evaluation
elevation = [10, 30, 60, 90]
dl_throughput = [52.3, 78.5, 89.2, 94.7]
ul_throughput = [18.7, 31.2, 38.6, 41.3]
sinr = [3.2, 8.5, 12.8, 15.2]

# Create figure with single-column width (3.5 inches)
fig, ax1 = plt.subplots(figsize=(3.5, 3.5))

# Primary axis: Throughput
ax1.set_xlabel('Satellite Elevation Angle (degrees)', fontsize=9, fontweight='normal')
ax1.set_ylabel('Throughput (Mbps)', fontsize=9, fontweight='normal')

# Plot downlink and uplink throughput
line1 = ax1.plot(elevation, dl_throughput, 'b-o', linewidth=1.5,
                 markersize=6, markerfacecolor='blue', markeredgecolor='blue',
                 label='Downlink Throughput', zorder=3)
line2 = ax1.plot(elevation, ul_throughput, 'r--s', linewidth=1.5,
                 markersize=6, markerfacecolor='red', markeredgecolor='red',
                 label='Uplink Throughput', zorder=3)

# Set axis limits and ticks
ax1.set_xlim([0, 100])
ax1.set_ylim([0, 100])
ax1.set_xticks([0, 20, 40, 60, 80, 100])
ax1.set_yticks([0, 20, 40, 60, 80, 100])

# Add grid with light gray color
ax1.grid(True, alpha=0.3, linestyle='-', linewidth=0.5, color='gray', zorder=1)

# Format tick labels
ax1.tick_params(axis='both', labelsize=8, direction='in', width=0.8)

# Secondary axis: SINR
ax2 = ax1.twinx()
ax2.set_ylabel('SINR (dB)', fontsize=9, fontweight='normal')

# Plot SINR
line3 = ax2.plot(elevation, sinr, 'g:^', linewidth=1.5,
                 markersize=6, markerfacecolor='green', markeredgecolor='green',
                 label='SINR', zorder=3)

# Set secondary axis limits and ticks
ax2.set_ylim([0, 16])
ax2.set_yticks([0, 4, 8, 12, 16])
ax2.tick_params(axis='y', labelsize=8, direction='in', width=0.8)

# Combined legend in upper left
lines = line1 + line2 + line3
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper left', fontsize=7, frameon=True,
          framealpha=0.9, edgecolor='gray', fancybox=False)

# Tight layout to remove excess whitespace
plt.tight_layout(pad=0.3)

# Create figures directory if it doesn't exist
os.makedirs('.', exist_ok=True)

# Save in multiple formats
print("Generating Figure 2: Performance Graph...")

# Save as PDF (vector format, preferred for IEEE)
plt.savefig('figure2_performance.pdf', dpi=300, bbox_inches='tight',
            format='pdf', backend='pdf')
print("✓ Saved: figure2_performance.pdf")

# Save as EPS (vector format, IEEE compatible)
plt.savefig('figure2_performance.eps', dpi=300, bbox_inches='tight',
            format='eps')
print("✓ Saved: figure2_performance.eps")

# Save as high-resolution PNG (raster backup)
plt.savefig('figure2_performance.png', dpi=600, bbox_inches='tight',
            format='png')
print("✓ Saved: figure2_performance.png (600 dpi)")

print("\nFigure 2 generation complete!")
print("Use figure2_performance.pdf or figure2_performance.eps for submission.")

# Display the figure (optional)
# plt.show()
