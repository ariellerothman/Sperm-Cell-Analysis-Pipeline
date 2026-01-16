"""TrackMate tracking CSV processing and visualization.

Handles conversion between TrackMate CSV formats (wide to long) and provides
visualization functions for overlaying tracks on image slices.
"""

import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from skimage import io
from .config import TRACKING_BLOCK_SIZE, FRAMES_TO_DISPLAY, MIN_TRACKS

def find_input_csv(cell_dir: str, organelle: str, cell_number: int) -> str:
    """Locate tracking CSV for a specific organelle and cell number.
    
    Uses flexible glob patterns to find CSVs with variations in naming:
    - Case insensitive: 'MO_tracking_16.csv', 'mo_tracking_16.csv'
    - Order flexible: 'tracking_MO_16.csv' or 'MO_tracking_16.csv'
    - Spacing flexible: 'MO tracking 16.csv' or 'MO_tracking_16.csv'
    
    Args:
        cell_dir: Directory containing CSV files.
        organelle: Organelle name (e.g., 'MO', 'mitochondria').
        cell_number: Sperm cell ID number.
    
    Returns:
        Path to matching CSV file.
    
    Raises:
        FileNotFoundError: If no matching CSV found.
    """
    # Try multiple flexible glob patterns
    patterns = [
        os.path.join(cell_dir, f"*{organelle}*tracking*{cell_number}*.csv"),
        os.path.join(cell_dir, f"*tracking*{organelle}*{cell_number}*.csv"),
        os.path.join(cell_dir, f"*{organelle}*{cell_number}*tracking*.csv"),
    ]
    
    matches = []
    for pattern in patterns:
        matches.extend(glob.glob(pattern, recursive=False))
    
    # Remove duplicates while preserving order
    seen = set()
    matches = [m for m in matches if not (m in seen or seen.add(m))]
    
    # Filter to CSV files only
    matches = [f for f in matches if f.lower().endswith('.csv')]

    if matches:
        print(f"✅ Found input CSV: {matches[0]}")
        return matches[0]

    # Print available CSVs to help debug
    debug_files = [f for f in os.listdir(cell_dir) if f.lower().endswith('.csv')]
    print(f"🧐 Available CSV files in {cell_dir}: {debug_files}")

    raise FileNotFoundError(f"🚫 Could not find CSV for {organelle} in {cell_dir}")

def move_tracks_horizontally(
    input_csv: str, output_csv: str, tracks_per_block: int = TRACKING_BLOCK_SIZE,
    label_prefix: str = "Tracks "
) -> None:
    """Reorganize TrackMate wide format CSV horizontally.
    
    TrackMate groups tracks in blocks (default 75 per block). This function
    merges blocks by renumbering columns.
    
    Args:
        input_csv: Path to input wide-format CSV.
        output_csv: Path to save reorganized CSV.
        tracks_per_block: Number of tracks per block in input CSV.
        label_prefix: Row label prefix to identify block separators.
    """
    df_raw = pd.read_csv(input_csv, header=0)
    blocks = []
    current_block_rows = []
    for _, row in df_raw.iterrows():
        if isinstance(row['Frame'], str) and row['Frame'].startswith(label_prefix):
            if current_block_rows:
                blocks.append(pd.DataFrame(current_block_rows))
                current_block_rows = []
            continue
        if pd.notnull(row['Frame']):
            current_block_rows.append(row.to_dict())
    if current_block_rows:
        blocks.append(pd.DataFrame(current_block_rows))
    final_df = pd.DataFrame()
    for i, block_df in enumerate(blocks):
        offset = i * tracks_per_block
        rename_map = {col: f"{col[0]}{offset + int(col[1:])}" for col in block_df.columns if col[1:].isdigit()}
        final_df = pd.concat([final_df, block_df.rename(columns=rename_map)], axis=1)
    final_df.to_csv(output_csv, index=False)

# === Convert wide format to long format ===
def wide_to_long(input_csv: str, output_csv: str, num_tracks: int) -> None:
    """Convert TrackMate wide format CSV to long format.
    
    Wide format has columns: Frame, X1, Y1, Flag1, X2, Y2, Flag2, ...
    Long format has columns: Frame, Track, X, Y, Flag
    
    Args:
        input_csv: Path to input wide-format CSV.
        output_csv: Path to save long-format CSV.
        num_tracks: Total number of tracks to expect.
    """
    df = pd.read_csv(input_csv)
    records = []
    
    for _, row in df.iterrows():
        frame = int(float(row['Frame']))
        for i in range(1, num_tracks + 1):
            x = row.get(f"X{i}")
            y = row.get(f"Y{i}")
            flag = row.get(f"Flag{i}")
            if pd.notnull(x) and pd.notnull(y):
                records.append({"Frame": frame, "Track": i, "X": x, "Y": y, "Flag": flag})
    pd.DataFrame(records).to_csv(output_csv, index=False)

# === Visualization function ===
def visualize_tracking(
    tiff_path: str, csv_path: str, frames_to_display: int = FRAMES_TO_DISPLAY,
    min_tracks: int = MIN_TRACKS, save_overlays: bool = True, output_dir: str = None
) -> str:
    """Display tracking overlays on image slices and optionally save them.
    
    Shows TIFF slices with tracking points marked as red circles and labeled
    with track IDs. Only displays frames with sufficient track count.
    
    Args:
        tiff_path: Path to TIFF stack file.
        csv_path: Path to tracking CSV (long format: Frame, Track, X, Y, Flag).
        frames_to_display: Maximum number of frames to show.
        min_tracks: Minimum number of tracks per frame to include.
        save_overlays: If True, save overlay images to disk.
        output_dir: Directory to save overlay images. If None, uses same dir as CSV.
    
    Returns:
        Path to directory containing saved overlays (or None if not saved).
    """
    stack = io.imread(tiff_path)
    df = pd.read_csv(csv_path)
    
    # Only keep rows with valid Track and Frame
    df = df[pd.notnull(df['Track']) & pd.notnull(df['Frame'])]
    
    # Count unique tracks per frame
    track_counts = df.groupby('Frame')['Track'].nunique()
    
    # Only keep frames with at least min_tracks unique tracks
    frames_with_tracks = track_counts[track_counts >= min_tracks].index.tolist()
    frames_with_tracks = sorted(frames_with_tracks)[:frames_to_display]
    
    # Determine output directory for overlays
    if save_overlays:
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(csv_path), "tracking_overlays")
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract organelle name from CSV filename for better organization
        csv_basename = os.path.basename(csv_path)
        if "long" in csv_basename:
            organelle_name = csv_basename.replace("_temp_long.csv", "").replace("_long.csv", "")
        else:
            organelle_name = "tracking"
        
        overlay_dir = os.path.join(output_dir, f"{organelle_name}_overlays")
        os.makedirs(overlay_dir, exist_ok=True)
    
    for frame_num in frames_with_tracks:
        i = int(frame_num) - 1  # Change to int(frame_num) if your stack is 0-based
        if i < 0 or i >= stack.shape[0]:
            continue
        
        img = stack[i]
        
        fig, ax = plt.subplots(figsize=(8, 8), dpi=100)
        ax.imshow(img, cmap='gray')
        
        frame_df = df[df['Frame'] == frame_num]
        for _, row in frame_df.iterrows():
            try:
                x = float(row['X'])
                y = float(row['Y'])
                ax.plot(x, y, 'ro', markersize=5)
                ax.text(x + 2, y + 2, str(int(row['Track'])), color='red', fontsize=8)
            except (ValueError, TypeError):
                continue
        
        ax.set_title(f"Slice {i+1} (Frame {int(frame_num)}, Tracks: {frame_df['Track'].nunique()})", fontsize=12)
        ax.axis('off')
        
        # Save overlay if requested
        if save_overlays:
            overlay_path = os.path.join(overlay_dir, f"frame_{int(frame_num):03d}_overlay.png")
            plt.savefig(overlay_path, bbox_inches='tight', dpi=100)
        
        plt.show()
        plt.close(fig)
    
    if save_overlays:
        print(f"✅ Tracking overlays saved to: {overlay_dir}")
        return overlay_dir
    else:
        return None
# === Full Tracking Pipeline ===
def run_tracking_pipeline(
    cell_number: int, base_dir: str, organelle: str = "MO", total_tracks: int = 400
) -> str:
    """Run complete tracking pipeline: find CSV, convert format, visualize.
    
    Args:
        cell_number: Sperm cell ID number.
        base_dir: Parent directory containing 'Sperm N' folders.
        organelle: Organelle name (e.g., 'MO', 'mitochondria').
        total_tracks: Total number of tracks in TrackMate output.
    
    Returns:
        Path to output long-format CSV file.
    
    Raises:
        FileNotFoundError: If required files not found.
    """
    from .utils import find_file_by_pattern
    
    cell_dir = os.path.join(base_dir, f"Sperm {cell_number}")

    # ✅ Find input CSV
    csv_in = find_input_csv(cell_dir, organelle, cell_number)

    # ✅ Find registered TIFF (needed for tracking visualization)
    try:
        tiff_in = find_file_by_pattern(cell_dir, organelle, cell_number, registered=True)
    except FileNotFoundError:
        tiff_in = None
        print(f"⚠️ No registered TIFF found for {organelle} (visualization skipped)")
    
    # ✅ Define intermediate CSV paths
    wide_csv = os.path.join(cell_dir, f"{organelle}_temp_wide.csv")
    long_csv = os.path.join(cell_dir, f"{organelle}_temp_long.csv")

    # 🔁 Run processing steps
    move_tracks_horizontally(csv_in, wide_csv)
    wide_to_long(wide_csv, long_csv, num_tracks=total_tracks)

    # 👁️ Visualization (optional)
    if tiff_in and os.path.exists(tiff_in):
        visualize_tracking(tiff_in, long_csv, frames_to_display=io.imread(tiff_in).shape[0])

    return long_csv

