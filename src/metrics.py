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
from .utils import get_centroid

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
            - sample_id, organelle_type, track_id (unique ID for each instance)
            - volume_um3, surface_area_um2, sphericity (morphological metrics)
            - centroid coordinates (z, y, x) in voxels
            - distances to pseudopod and nucleus (spatial relationships)
            - aspect_ratio (AABB - axis-aligned bounding box shape descriptor)
            - obb_aspect_ratio (OBB - object-oriented bounding box, aligned to principal axes via PCA)
            - direction_vector components (z, y, x) (orientation for pseudopod only)
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
                print(f"Warning: No valid markers placed for {organelle_name} (loaded {rows_loaded}, skipped {rows_skipped})")
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
        # Only measure distances for mitochondria and MO organelles
        if organelle_name in ["mitochondria", "MO"]:
            # Convert to physical coordinates (micrometers) before computing distance
            delta_to_pod = (centroid - pseudopod_centroid) * np.array([slice_thickness_um, pixel_size_um, pixel_size_um])
            dist_to_pod = np.linalg.norm(delta_to_pod)
            delta_to_nuc = (centroid - nucleus_centroid) * np.array([slice_thickness_um, pixel_size_um, pixel_size_um])
            dist_to_nuc = np.linalg.norm(delta_to_nuc)
        else:
            dist_to_pod = np.nan
            dist_to_nuc = np.nan

        min_z, min_y, min_x, max_z, max_y, max_x = region.bbox
        depth_um = (max_z - min_z) * slice_thickness_um
        height_um = (max_y - min_y) * pixel_size_um
        width_um = (max_x - min_x) * pixel_size_um
        dims = np.array([depth_um, height_um, width_um])
        aspect_ratio = np.max(dims) / np.min(dims) if np.all(dims > 0) else np.nan

        # === Compute Object-Oriented Bounding Box (OBB) via PCA ===
        mask = (labels == track_id)
        coords = np.argwhere(mask)  # Get all voxel coordinates in this region
        
        if len(coords) > 3:  # Need at least 4 points for meaningful PCA
            # Apply voxel spacing to get physical coordinates
            coords_physical = coords * np.array([slice_thickness_um, pixel_size_um, pixel_size_um])
            
            # Center the coordinates using physical space centroid
            centroid_physical = centroid * np.array([slice_thickness_um, pixel_size_um, pixel_size_um])
            coords_centered = coords_physical - centroid_physical
            
            # Perform PCA to get principal axes
            pca = PCA(n_components=3)
            pca.fit(coords_centered)
            principal_axes = pca.components_  # Shape: (3, 3) - rows are principal axes
            
            # Project coordinates onto principal axes
            projected = np.dot(coords_centered, principal_axes.T)
            
            # Compute OBB dimensions along each principal axis
            obb_half_extents = np.max(np.abs(projected), axis=0)
            obb_dims = 2 * obb_half_extents  # Full dimensions
            
            # Store principal axes as rotation matrix (columns are eigenvectors)
            rotation_matrix = principal_axes.T  # Shape: (3, 3)
            
            # Compute rotation angles (Euler angles in ZYX order for medical imaging)
            # Roll (rotation around Z), Pitch (around Y), Yaw (around X)
            sy = np.sqrt(rotation_matrix[0, 0]**2 + rotation_matrix[1, 0]**2)
            singular = sy < 1e-6
            
            if not singular:
                yaw = np.arctan2(rotation_matrix[1, 0], rotation_matrix[0, 0])
                pitch = np.arctan2(-rotation_matrix[2, 0], sy)
                roll = np.arctan2(rotation_matrix[2, 1], rotation_matrix[2, 2])
            else:
                yaw = np.arctan2(-rotation_matrix[1, 0], rotation_matrix[1, 1])
                pitch = np.arctan2(-rotation_matrix[2, 0], sy)
                roll = 0.0
            
            obb_yaw_deg = np.degrees(yaw)
            obb_pitch_deg = np.degrees(pitch)
            obb_roll_deg = np.degrees(roll)
            
            # OBB aspect ratio (ratio of largest to smallest dimension)
            obb_aspect_ratio = np.max(obb_dims) / np.min(obb_dims) if np.all(obb_dims > 0) else np.nan
        else:
            # Fallback to AABB if not enough points
            obb_dims = dims
            obb_aspect_ratio = aspect_ratio
            obb_yaw_deg = 0.0
            obb_pitch_deg = 0.0
            obb_roll_deg = 0.0
        try:
            verts, faces, *_ = marching_cubes(mask.astype(np.uint8), level=0.5,
                                              spacing=(slice_thickness_um, pixel_size_um, pixel_size_um))
            surface_area = mesh_surface_area(verts, faces)
            sphericity = ((math.pi ** (1 / 3)) * (6 * volume) ** (2 / 3)) / surface_area if surface_area > 0 else np.nan
        except Exception:
            surface_area = sphericity = np.nan

        results.append({
            "sample_id": sample_id,
            "organelle_type": organelle_name,
            "track_id": track_id,
            "volume_um3": volume,
            "surface_area_um2": surface_area,
            "sphericity": sphericity,
            "centroid_z_um": centroid[0] * slice_thickness_um,
            "centroid_y_um": centroid[1] * pixel_size_um,
            "centroid_x_um": centroid[2] * pixel_size_um,
            "distance_to_pseudopod": dist_to_pod,
            "distance_to_nucleus": dist_to_nuc,
            "aspect_ratio": aspect_ratio,
            "obb_aspect_ratio": obb_aspect_ratio,
            "direction_vector_z": direction_vector[0],
            "direction_vector_y": direction_vector[1],
            "direction_vector_x": direction_vector[2]
        })
    return pd.DataFrame(results)


def get_metrics_summary(df: pd.DataFrame) -> dict:
    """Generate QC summary from metrics DataFrame.
    
    Provides key statistics:
    - Single organelles: volume
    - Multiple organelles: count per type
    - Data validation: warnings for NaN/zero values
    
    Args:
        df: DataFrame from compute_organelle_metrics()
    
    Returns:
        Dictionary with summary statistics and validation warnings
    """
    summary = {}
    warnings = []
    
    # Single organelle volumes
    for org in ["pseudopod", "nucleus"]:
        org_data = df[df["organelle_type"] == org]
        if len(org_data) > 0:
            vol = org_data.iloc[0]["volume_um3"]
            if pd.isna(vol):
                warnings.append(f"    {org}: volume is NaN")
                summary[f"{org}_volume_um3"] = np.nan
            elif vol == 0:
                warnings.append(f"    {org}: volume is 0")
                summary[f"{org}_volume_um3"] = 0.0
            else:
                summary[f"{org}_volume_um3"] = round(vol, 2)
    
    # Multiple organelle counts
    for org in ["mitochondria", "MO"]:
        org_data = df[df["organelle_type"] == org]
        count = len(org_data)
        summary[f"{org}_count"] = count
        
        if count > 0:
            # Check for suspicious values
            zero_volumes = (org_data["volume_um3"] == 0).sum()
            nan_volumes = org_data["volume_um3"].isna().sum()
            
            if zero_volumes > 0:
                warnings.append(f"    {org}: {zero_volumes}/{count} instances have zero volume")
            if nan_volumes > 0:
                warnings.append(f"    {org}: {nan_volumes}/{count} instances have NaN volume")
    
    # Sperm cell volume
    sperm_data = df[df["organelle_type"] == "sperm_cell"]
    if len(sperm_data) > 0:
        vol = sperm_data.iloc[0]["volume_um3"]
        summary["sperm_cell_volume_um3"] = round(vol, 2) if not pd.isna(vol) else np.nan
    
    summary["validation_warnings"] = warnings
    return summary


def validate_metrics(df: pd.DataFrame) -> list:
    """Validate metrics for data quality issues.
    
    Args:
        df: DataFrame from compute_organelle_metrics()
    
    Returns:
        List of validation warnings/errors
    """
    issues = []
    
    # Check for empty DataFrame
    if len(df) == 0:
        issues.append("ERROR: No metrics computed (empty DataFrame)")
        return issues
    
    # Check for missing columns
    required_cols = ["volume_um3", "organelle_type"]
    for col in required_cols:
        if col not in df.columns:
            issues.append(f"ERROR: Missing required column '{col}'")
    
    # Check for NaN volumes
    nan_mask = df["volume_um3"].isna()
    if nan_mask.sum() > 0:
        bad_orgs = df[nan_mask]["organelle_type"].unique()
        issues.append(f"WARNING: {nan_mask.sum()} rows have NaN volumes: {', '.join(bad_orgs)}")
    
    # Check for zero or negative volumes
    zero_mask = df["volume_um3"] <= 0
    if zero_mask.sum() > 0:
        bad_orgs = df[zero_mask]["organelle_type"].unique()
        issues.append(f"WARNING: {zero_mask.sum()} rows have zero/negative volumes: {', '.join(bad_orgs)}")
    
    # Check for mitochondria/MO without distance data
    for org in ["mitochondria", "MO"]:
        org_data = df[df["organelle_type"] == org]
        if len(org_data) > 0:
            missing_dist = org_data["distance_to_pseudopod"].isna().sum()
            if missing_dist > 0:
                issues.append(f"WARNING: {org}: {missing_dist}/{len(org_data)} missing distance_to_pseudopod")
    
    return issues