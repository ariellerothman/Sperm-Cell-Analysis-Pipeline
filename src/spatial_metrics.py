"""Spatial metrics computation for sperm cells.

Computes distances and angles relative to reference points in the sample.
All voxel sizes are imported from config.py to ensure consistency.
"""

import os
import numpy as np
from skimage import io, measure
from read_roi import read_roi_file
from sklearn.decomposition import PCA
import math
import glob

from .config import PIXEL_SIZE_UM, SLICE_THICKNESS_UM, VOXEL_SIZE

def find_roi_file(folder_path: str) -> str:
    """Find and return the path to a single ROI file in a folder.
    
    Args:
        folder_path: Directory containing ROI file(s).
    
    Returns:
        Path to the ROI file.
    
    Raises:
        FileNotFoundError: If no ROI file found.
        ValueError: If multiple ROI files found.
    """
    roi_files = glob.glob(os.path.join(folder_path, "*.roi"))
    if len(roi_files) == 0:
        raise FileNotFoundError(f"No ROI file found in: {folder_path}")
    if len(roi_files) > 1:
        raise ValueError(f"Multiple ROI files found. Please ensure only one exists in: {folder_path}")
    return roi_files[0]

def get_crop_offset_from_roi(roi_path: str) -> tuple:
    """Extract crop offset coordinates from an ImageJ ROI file.
    
    When a sperm cell is cropped from a larger full image, the crop boundaries
    are stored in the ROI file. These offsets are needed to convert coordinates
    from the cropped image space back to the global/full image space.
    
    For example: If the crop started at Y=100, X=200 in the full image,
    then a point at (Y=50, X=75) in the cropped image is actually at
    (Y=150, X=275) in the full image.
    
    Args:
        roi_path: Path to ImageJ ROI file (typically .roi format).
    
    Returns:
        Tuple of (offset_y, offset_x) in pixels. These are the top-left corner
        coordinates of where the crop started in the original full image.
    
    Raises:
        ValueError: If ROI file is empty or malformed.
    """
    roi = read_roi_file(roi_path)
    if not roi:
        raise ValueError("No ROI found.")
    roi_data = list(roi.values())[0]
    return int(roi_data["top"]), int(roi_data["left"])  # (y, x)

def get_largest_centroid(path: str) -> np.ndarray:
    """Extract centroid of the largest connected component in a binary mask.
    
    Args:
        path: Path to binary mask TIFF file.
    
    Returns:
        Centroid coordinates as (z, y, x) numpy array.
    
    Raises:
        ValueError: If mask contains no objects.
    """
    img = io.imread(path)
    binary = (img > 0).astype(np.uint8)
    regions = measure.regionprops(measure.label(binary))
    if not regions:
        raise ValueError("No objects in mask.")
    largest = max(regions, key=lambda r: r.area)
    return np.array(largest.centroid)  # (z, y, x)

def get_direction_vector(mask: np.ndarray) -> tuple:
    """Compute principal direction vector of a 3D pseudopod using PCA.
    
    The pseudopod (sperm tail) extends in a particular direction toward or away
    from the spermathecal valve. This function determines that orientation using
    Principal Component Analysis (PCA) on the 3D structure.
    
    **Biological Interpretation:**
    - The direction vector indicates which way the sperm is oriented
    - Used to calculate angle between pseudopod orientation and spermathecal valve center
    - Helps determine if sperm is positioned to move toward the egg for fertilization
    
    Args:
        mask: 3D binary array where True indicates pseudopod voxels.
    
    Returns:
        Tuple of (direction_vector, tip_point) in physical coordinates (micrometers).
        - direction_vector: Principal component (orientation of pseudopod elongation)
        - tip_point: The furthest extent of pseudopod along principal direction
        Returns (NaN array, NaN array) if fewer than 3 voxels in mask.
    """
    coords = np.argwhere(mask > 0)
    if len(coords) < 3:
        return np.array([np.nan] * 3), np.array([np.nan] * 3)
    coords_phys = coords * np.array(VOXEL_SIZE)
    pca = PCA(n_components=3).fit(coords_phys)
    direction = pca.components_[0]
    tip = coords_phys[np.argmin(coords_phys @ direction)]  # tip = furthest back projection
    return direction, tip

def angle_between_vectors(v1: np.ndarray, v2: np.ndarray) -> float:
    """Compute angle between two 3D vectors in degrees.
    
    Args:
        v1: First 3D vector.
        v2: Second 3D vector.
    
    Returns:
        Angle in degrees (0 to 180).
    """
    cos_angle = np.clip(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)), -1.0, 1.0)
    return np.rad2deg(np.arccos(cos_angle))

def compute_spatial_metrics(
    sperm_cell_path: str, pseudopod_path: str, nucleus_path: str,
    roi_path: str, reference_point_xyz: list
) -> dict:
    """Compute spatial metrics for sperm cell relative to reference point.
    
    **Coordinate System Note:**
    The sperm cell images are cropped from a larger full image. All coordinates
    must be converted from cropped space back to global space to align with the
    reference point. This is done using the ROI offset extracted from the ROI file.
    
    Args:
        sperm_cell_path: Path to sperm cell binary mask TIFF (cropped image space).
        pseudopod_path: Path to pseudopod binary mask TIFF (cropped image space).
        nucleus_path: Path to nucleus binary mask TIFF (cropped image space).
        roi_path: Path to ImageJ ROI file (contains crop offset that maps cropped
                 coordinates to global image coordinates).
        reference_point_xyz: Coordinates of spermathecal valve center [Z, Y, X]
                            in voxels (global image space).
    
    Returns:
        Dictionary with keys:
            - centroid_global: Sperm cell centroid in global coordinates
            - pseudopod_tip_global: Pseudopod tip in global coordinates
            - distance_centroid_to_target_um: Distance in micrometers
            - distance_pseudopod_tip_to_target_um: Distance in micrometers
            - angle_between_direction_and_target_vector_deg: Angle in degrees
    """
    # Get offsets from ROI (assumes crop from full image)
    offset_y, offset_x = get_crop_offset_from_roi(roi_path)

    # Load centroid data from cropped image space
    centroid_crop = get_largest_centroid(sperm_cell_path)
    nucleus_crop = get_largest_centroid(nucleus_path)

    # Convert from cropped coordinates to global coordinates by adding offsets
    # This aligns the sperm cell with the reference point (spermathecal valve center)
    # which is defined in the original full image space
    centroid_global = np.array([centroid_crop[0], centroid_crop[1] + offset_y, centroid_crop[2] + offset_x])
    nucleus_global  = np.array([nucleus_crop[0], nucleus_crop[1] + offset_y, nucleus_crop[2] + offset_x])

    # Get pseudopod tip and direction
    pseudopod_mask = io.imread(pseudopod_path) > 0
    direction_vector, tip_phys = get_direction_vector(pseudopod_mask)

    # Map pseudopod tip to global coordinates
    pseudopod_tip = tip_phys / np.array(VOXEL_SIZE)
    pseudopod_tip[1] += offset_y
    pseudopod_tip[2] += offset_x

    # Reference point
    reference_point = np.array(reference_point_xyz)

    # Distances
    dist_centroid = np.linalg.norm((centroid_global - reference_point) * np.array(VOXEL_SIZE))
    dist_tip = np.linalg.norm((pseudopod_tip - reference_point) * np.array(VOXEL_SIZE))

    # Angle between vectors
    vector_to_ref = reference_point - centroid_global
    angle_deg = angle_between_vectors(vector_to_ref, direction_vector)

    return {
        "centroid_global": centroid_global,
        "pseudopod_tip_global": pseudopod_tip,
        "distance_centroid_to_target_um": dist_centroid,
        "distance_pseudopod_tip_to_target_um": dist_tip,
        "angle_between_direction_and_target_vector_deg": angle_deg
    }