"""Central configuration file for sperm cell analysis pipeline.

Defines all shared parameters including voxel dimensions, organelle thresholds,
tracking parameters, mesh extraction settings, and video rendering options.

All modules should import configuration from this file rather than hardcoding
parameter values, ensuring consistency across the pipeline.
"""

# ============================================================================
# MICROSCOPY CALIBRATION
# ============================================================================
PIXEL_SIZE_UM = 0.016
"""Lateral pixel size in micrometers (XY plane resolution)."""

SLICE_THICKNESS_UM = 0.05
"""Axial slice thickness in micrometers (Z resolution)."""

VOXEL_VOLUME = (PIXEL_SIZE_UM ** 2) * SLICE_THICKNESS_UM
"""Voxel volume in cubic micrometers. Derived from pixel size and slice thickness."""

VOXEL_SIZE = (SLICE_THICKNESS_UM, PIXEL_SIZE_UM, PIXEL_SIZE_UM)  # (z, y, x)
"""Voxel dimensions as tuple (z_um, y_um, x_um). Used for all 3D calculations."""


# ============================================================================
# ORGANELLE DEFINITIONS AND SEGMENTATION
# ============================================================================
ORGANELLES = [
    {"name": "mitochondria", "color": "orange", "opacity": 0.7, "blur": 0.0},
    {"name": "MO", "color": "purple", "opacity": 0.9, "blur": 0.0},
    {"name": "pseudopod", "color": "darkgreen", "opacity": 0.9, "blur": 3.0},
    {"name": "nucleus", "color": "black", "opacity": 0.9, "blur": 0.0},
    {"name": "sperm_cell", "color": "lightgreen", "opacity": 0.2, "blur": 3.0},
]
"""List of organelle definitions with rendering properties."""

ORGANELLE_THRESHOLD = 128
"""Binary threshold for organelle segmentation in intensity-based masks.

Typical range: 100-200. Lower values include more dim regions, higher values
only keep brightest structures. Tune based on signal-to-noise ratio in your
microscopy images. Can also use 'otsu' for automatic Otsu thresholding."""


# ============================================================================
# TRACKING PARAMETERS (TrackMate CSV processing)
# ============================================================================
TRACKING_BLOCK_SIZE = 75
"""Default block size for TrackMate track reorganization.

TrackMate splits tracks into blocks of this size during export. Used when
reorganizing tracks from multiple blocks back into continuous tracks."""

FRAMES_TO_DISPLAY = 200
"""Maximum number of frames to display in tracking visualization.

Limits visualization memory for large datasets. Set higher for better
temporal resolution on shorter sequences."""

MIN_TRACKS = 2
"""Minimum number of tracks required to process tracking data.

Datasets with fewer tracks than this threshold are skipped."""


# ============================================================================
# 3D MESH EXTRACTION PARAMETERS
# ============================================================================
MESH_MIN_SIZE = 100
"""Minimum voxel count for objects to include in 3D mesh.

Removes small noise. Typical range: 50-500 depending on organelle size."""

MESH_THRESHOLD = 'otsu'
"""Thresholding method for binary mask generation before meshing.

Options: 'otsu' (auto), or numeric threshold (0-255 for 8-bit, or intensity value)."""

MESH_BLUR = 0.0
"""Gaussian blur sigma applied before thresholding (micrometers).

Smooths small noise in binary mask. Range: 0.0-3.0. Higher = more smoothing."""

MESH_CLOSE_RADIUS = 0
"""Morphological closing radius in voxels.

Fills small holes in segmentation. Range: 0 (no closing) to 3-5."""


# ============================================================================
# VIDEO RENDERING PARAMETERS
# ============================================================================
VIDEO_ZOOM_FACTOR = 2.0
"""Camera zoom factor for orbital rendering (>1 = zoomed out, <1 = zoomed in)."""

VIDEO_NUM_FRAMES = 60
"""Number of frames for complete 360° rotation video."""

VIDEO_FPS = 10
"""Frames per second for output video file."""


# ============================================================================
# SPATIAL REFERENCE POINTS
# ============================================================================
REFERENCE_POINT_XYZ = [58, 1256, 2464]
"""3D reference point coordinates [Z, Y, X] in voxels.

Represents the center of the spermathecal valve, determined by:
1. Identifying the centermost Z-slice where the valve is visible
2. Finding the XY coordinates of the valve center on that slice
3. Recording as [Z_slice, Y_pixel, X_pixel]

This reference point is used to compute spatial metrics:
- Distance from sperm cell centroid to spermathecal valve center
- Distance from pseudopod tip to spermathecal valve center
- Angle between pseudopod orientation and direction toward valve

Update these values if analyzing different samples or imaging regions."""
