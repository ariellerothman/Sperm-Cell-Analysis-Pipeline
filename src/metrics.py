"""Organelle metrics computation module.

Computes morphological and spatial metrics for organelles in sperm cells,
including volume, surface area, sphericity, centroid location, and distances
to reference structures (pseudopod, nucleus).
"""

import numpy as np
import os
import pandas as pd
import math
from skimage import io, measure, segmentation
from scipy import ndimage as ndi
from skimage.measure import marching_cubes, mesh_surface_area
from sklearn.decomposition import PCA
from .config import PIXEL_SIZE_UM, SLICE_THICKNESS_UM, VOXEL_VOLUME, ORGANELLE_THRESHOLD

def get_centroid(path: str) -> np.ndarray:
    """Extract centroid of largest connected component in a binary mask.
    
    Args:
        path: Path to binary mask TIFF file.
    
    Returns:
        Centroid coordinates as (z, y, x) numpy array.
        Returns array of NaNs if no objects found.
    """
    mask = io.imread(path)
    mask = (mask > 0).astype(np.uint8)
    props = measure.regionprops(measure.label(mask))
    return np.array(props[0].centroid) if props else np.array([np.nan] * 3)

def compute_direction_vector(binary_mask: np.ndarray, voxel_spacing: tuple = None) -> np.ndarray:
    """Compute principal direction vector using PCA.
    
    Args:
        binary_mask: 3D binary array where True indicates the object.
        voxel_spacing: Tuple of (z_um, y_um, x_um) voxel dimensions.
                      If None, uses uniform spacing of 1.0.
    
    Returns:
        Normalized principal component direction vector.
        Returns NaN array if fewer than 3 voxels in mask.
    """
    if voxel_spacing is None:
        voxel_spacing = (1.0, 1.0, 1.0)
    coords = np.argwhere(binary_mask > 0)
    coords_physical = coords * np.array(voxel_spacing)
    if coords_physical.shape[0] < 3:
        return np.array([np.nan] * 3)
    pca = PCA(n_components=3)
    pca.fit(coords_physical)
    return pca.components_[0] / np.linalg.norm(pca.components_[0])

def compute_organelle_metrics(
    organelle_name: str, segmentation_path: str, csv_path: str,
    pseudopod_centroid: np.ndarray, nucleus_centroid: np.ndarray, 
    sample_id: str
) -> pd.DataFrame:
    """Compute comprehensive metrics for all labeled organelles in a stack.
    
    **Segmentation Strategy:**
    - **Single organelles** (nucleus, pseudopod, sperm_cell): Extracted as largest 
      connected component from binary mask.
    - **Multiple organelles** (mitochondria, MO): Uses watershed segmentation with 
      markers from tracking CSV. Each tracking point (Frame, X, Y, Track ID) acts as 
      a seed marker. Watershed groups all white pixels connected to each marker into 
      individual organelles, allowing tracking of multiple instances throughout the Z-stack.
    
    Args:
        organelle_name: Name of organelle. Types:
            - Single: 'nucleus', 'pseudopod', 'sperm_cell' (always 1 per cell)
            - Multiple: 'mitochondria', 'MO' (multiple instances per cell)
        segmentation_path: Path to binary mask TIFF (0-255 or 0-1).
        csv_path: Path to tracking CSV (Frame, X, Y, Track columns) or None.
                 Required for multiple organelles, ignored for single organelles.
        pseudopod_centroid: Reference centroid for pseudopod distance calculations.
        nucleus_centroid: Reference centroid for nucleus distance calculations.
        sample_id: Sample identifier string (e.g., 'sperm_16').
    
    Returns:
        DataFrame with one row per labeled organelle object, containing:
            - Sample_ID, Organelle_Type, Track_ID (unique ID for each instance)
            - Volume_µm3, Surface_Area_µm2, Sphericity (morphological metrics)
            - Centroid coordinates (z, y, x) in voxels
            - Distances to pseudopod and nucleus (spatial relationships)
            - BoundingBox_Volume_µm3, Density, Aspect_Ratio (shape descriptors)
            - Direction_Vector components (z, y, x) (orientation for pseudopod only)
    """
    # --- Load stack ---
    binary_stack = io.imread(segmentation_path)
    # Use threshold from config - tuning guide:
    # Lower (80-100) = more/smaller objects; Higher (150+) = larger objects only
    binary_stack = (binary_stack > ORGANELLE_THRESHOLD).astype(np.uint8)

    # --- Use config voxel sizes ---
    slice_thickness_um = SLICE_THICKNESS_UM
    pixel_size_um = PIXEL_SIZE_UM
    voxel_volume = VOXEL_VOLUME

    # --- Labeling Strategy ---
    if organelle_name in ["pseudopod", "nucleus", "sperm_cell"]:
        # SINGLE ORGANELLES: Extract only the largest connected component
        # These structures always appear once per sperm cell
        labeled = measure.label(binary_stack)
        regions = measure.regionprops(labeled)
        if len(regions) > 1:
            largest = max(regions, key=lambda r: r.area)
            binary_stack[:] = 0
            coords = tuple(zip(*largest.coords))
            binary_stack[coords] = 1
        labels = measure.label(binary_stack)
    else:
        # MULTIPLE ORGANELLES: Use watershed segmentation with tracking markers
        # Mitochondria and MO can have multiple instances per cell
        if csv_path and os.path.exists(csv_path):
            # Tracking CSV provides seed markers for each organelle instance
            # Each row = one tracking point (Frame, X, Y, Track ID)
            # Algorithm:
            #   1. Place marker at each tracked point with its Track ID
            #   2. Run watershed to grow from each seed until hitting black pixels
            #   3. Each organelle gets labeled with its original Track ID
            df = pd.read_csv(csv_path)
            markers = np.zeros(binary_stack.shape, dtype=np.int32)
            
            # Place markers at tracking coordinates - one unique ID per organelle
            rows_loaded = 0
            rows_skipped = 0
            for _, row in df.iterrows():
                if (not str(row.get("Frame", "")).strip() or
                    not str(row.get("X", "")).strip() or
                    not str(row.get("Y", "")).strip() or
                    not str(row.get("Track", "")).strip()):
                    rows_skipped += 1
                    continue
                try:
                    z = int(float(row["Frame"])) - 1  # Frame is 1-indexed from TrackMate, convert to 0-indexed
                    x = int(float(row["X"]))
                    y = int(float(row["Y"]))
                    track = int(float(row["Track"]))  # Unique ID for this organelle instance
                except ValueError as e:
                    rows_skipped += 1
                    continue
                if 0 <= z < binary_stack.shape[0] and 0 <= y < binary_stack.shape[1] and 0 <= x < binary_stack.shape[2]:
                    markers[z, y, x] = track
                    rows_loaded += 1
                else:
                    rows_skipped += 1
            
            if rows_loaded == 0:
                print(f"⚠️  Warning: No valid markers placed for {organelle_name} (loaded {rows_loaded}, skipped {rows_skipped})")
                labels = measure.label(binary_stack)
            else:
                # Watershed algorithm: Groups all white pixels connected to each marker into one organelle
                # Output labels match input marker IDs (Track IDs from CSV)
                # This allows us to track individual organelles from frame to frame
                distance = ndi.distance_transform_edt(binary_stack)
                labels = segmentation.watershed(-distance, markers, mask=binary_stack)
        else:
            # Fallback: No tracking data, use simple connected components
            labels = measure.label(binary_stack)

    cell_axis_vector = nucleus_centroid - pseudopod_centroid
    cell_length = np.linalg.norm(cell_axis_vector)
    cell_axis_unit = cell_axis_vector / cell_length if cell_length != 0 else np.array([0, 0, 0])

    direction_vector = [np.nan] * 3
    if organelle_name == "pseudopod":
        direction_vector = compute_direction_vector(
            binary_stack, voxel_spacing=(slice_thickness_um, pixel_size_um, pixel_size_um))

    results = []
    for region in measure.regionprops(labels):
        track_id = region.label
        volume = region.area * voxel_volume
        centroid = np.array(region.centroid)
        dist_to_pod = np.linalg.norm(centroid - pseudopod_centroid)
        dist_to_nuc = np.linalg.norm(centroid - nucleus_centroid)

        min_z, min_y, min_x, max_z, max_y, max_x = region.bbox
        depth_um = (max_z - min_z) * slice_thickness_um
        height_um = (max_y - min_y) * pixel_size_um
        width_um = (max_x - min_x) * pixel_size_um
        bbox_volume = depth_um * height_um * width_um
        density = volume / bbox_volume if bbox_volume > 0 else np.nan
        dims = np.array([depth_um, height_um, width_um])
        aspect_ratio = np.max(dims) / np.min(dims) if np.all(dims > 0) else np.nan

        mask = (labels == track_id)
        try:
            verts, faces, *_ = marching_cubes(mask.astype(np.uint8), level=0.5,
                                              spacing=(slice_thickness_um, pixel_size_um, pixel_size_um))
            surface_area = mesh_surface_area(verts, faces)
            sphericity = ((math.pi ** (1 / 3)) * (6 * volume) ** (2 / 3)) / surface_area if surface_area > 0 else np.nan
        except Exception:
            surface_area = sphericity = np.nan

        results.append({
            "Sample_ID": sample_id,
            "Organelle_Type": organelle_name,
            "Track_ID": track_id,
            "Volume_µm3": volume,
            "Surface_Area_µm2": surface_area,
            "Sphericity": sphericity,
            "Centroid_z": centroid[0],
            "Centroid_y": centroid[1],
            "Centroid_x": centroid[2],
            "Distance_to_Pseudopod": dist_to_pod,
            "Distance_to_Nucleus": dist_to_nuc,
            "BoundingBox_Volume_µm3": bbox_volume,
            "Density": density,
            "Aspect_Ratio": aspect_ratio,
            "Direction_Vector_z": direction_vector[0],
            "Direction_Vector_y": direction_vector[1],
            "Direction_Vector_x": direction_vector[2]
        })
    return pd.DataFrame(results)