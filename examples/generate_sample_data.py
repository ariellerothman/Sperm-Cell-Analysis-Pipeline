#!/usr/bin/env python3
"""
Generate synthetic sample data for the Sperm Cell Analysis Pipeline.

This script creates minimal synthetic 3D masks for testing and demonstration,
without requiring the full dataset.

Usage:
    python examples/generate_sample_data.py
"""

import os
import numpy as np
from skimage import io
import pandas as pd

def create_sample_sperm_data(output_dir="examples/sample_sperm_001"):
    """
    Generate synthetic sample data for a single sperm cell.
    
    Creates:
    - Binary masks (nucleus, pseudopod, mitochondria, sperm_cell)
    - Tracking CSV for mitochondria
    
    Args:
        output_dir: Directory to save sample data
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Create small synthetic 3D stacks (20 x 64 x 64 voxels = tiny but functional)
    z_size, y_size, x_size = 20, 64, 64
    
    # 1. Sperm cell boundary (large ellipsoid)
    sperm_stack = np.zeros((z_size, y_size, x_size), dtype=np.uint8)
    for z in range(z_size):
        z_norm = (z - z_size / 2) / (z_size / 2)
        for y in range(y_size):
            for x in range(x_size):
                y_norm = (y - y_size / 2) / (y_size / 4)
                x_norm = (x - x_size / 2) / (x_size / 4)
                dist = np.sqrt(z_norm**2 + y_norm**2 + x_norm**2)
                if dist < 1.0:
                    sperm_stack[z, y, x] = 255
    io.imsave(os.path.join(output_dir, "Sperm Cell_stack_1.tif"), sperm_stack)
    
    # 2. Nucleus (small sphere at one end)
    nucleus_stack = np.zeros((z_size, y_size, x_size), dtype=np.uint8)
    nuc_z, nuc_y, nuc_x = 5, 32, 32
    nuc_radius = 4
    for z in range(z_size):
        for y in range(y_size):
            for x in range(x_size):
                dist = np.sqrt((z - nuc_z)**2 + (y - nuc_y)**2 + (x - nuc_x)**2)
                if dist < nuc_radius:
                    nucleus_stack[z, y, x] = 255
    io.imsave(os.path.join(output_dir, "nucleus_stack_1.tif"), nucleus_stack)
    
    # 3. Pseudopod (elongated structure)
    pseudopod_stack = np.zeros((z_size, y_size, x_size), dtype=np.uint8)
    for z in range(z_size):
        pod_y = 15 + z * 0.5
        for y in range(y_size):
            for x in range(x_size):
                y_dist = abs(y - pod_y)
                x_dist = abs(x - 48)
                if y_dist < 3 and x_dist < 8:
                    pseudopod_stack[z, y, x] = 255
    io.imsave(os.path.join(output_dir, "Pseudopod_stack_1.tif"), pseudopod_stack)
    
    # 4. Mitochondria (multiple small spheres tracked across z)
    mito_stack = np.zeros((z_size, y_size, x_size), dtype=np.uint8)
    mito_radius = 2
    
    # Create 3 mitochondria with simple linear motion
    mito_positions = [
        [(10, 20, 25), (11, 21, 25), (12, 22, 25)],  # Mito 1
        [(10, 40, 40), (11, 40, 41), (12, 41, 42)],  # Mito 2
        [(8, 30, 30), (10, 30, 31), (12, 31, 32)],   # Mito 3
    ]
    
    tracking_data = []
    for mito_id, trajectory in enumerate(mito_positions, start=1):
        for frame_idx, (z, y, x) in enumerate(trajectory, start=1):
            # Create sphere
            for dz in range(-mito_radius, mito_radius + 1):
                for dy in range(-mito_radius, mito_radius + 1):
                    for dx in range(-mito_radius, mito_radius + 1):
                        if z + dz < z_size and y + dy < y_size and x + dx < x_size:
                            if (dz**2 + dy**2 + dx**2) <= mito_radius**2:
                                mito_stack[z + dz, y + dy, x + dx] = 255
            
            # Record tracking point
            tracking_data.append({
                "Frame": frame_idx,
                "X": x,
                "Y": y,
                "Track": mito_id
            })
    
    io.imsave(os.path.join(output_dir, "mitochondria_stack_1.tif"), mito_stack)
    
    # Save tracking CSV
    tracking_df = pd.DataFrame(tracking_data)
    tracking_csv = os.path.join(output_dir, "Mito tracking", "temp_long.csv")
    os.makedirs(os.path.dirname(tracking_csv), exist_ok=True)
    tracking_df.to_csv(tracking_csv, index=False)
    
    print(f"Sample data created in: {output_dir}")
    print(f"  - Sperm Cell_stack_1.tif ({sperm_stack.shape})")
    print(f"  - nucleus_stack_1.tif ({nucleus_stack.shape})")
    print(f"  - Pseudopod_stack_1.tif ({pseudopod_stack.shape})")
    print(f"  - mitochondria_stack_1.tif ({mito_stack.shape})")
    print(f"  - Mito tracking/temp_long.csv (3 mitochondria tracked)")

if __name__ == "__main__":
    create_sample_sperm_data()
