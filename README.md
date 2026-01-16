# Sperm Cell 3D Morphometric Analysis Pipeline

A comprehensive Python pipeline for automated 3D morphometric analysis of sperm cells from scanning electron microscopy (SEM) image stacks. This tool processes segmented organelle masks, tracking data, and microscopy parameters to compute detailed cellular and organellar metrics, enabling quantitative assessment of sperm cell morphology and spatial organization.

**Key Features:**
- 🔍 **Multi-organelle analysis** with automatic single vs. multiple instance detection
- 📊 **Comprehensive metrics** including volume, surface area, sphericity, density, and spatial relationships
- 🎬 **3D visualization** with interactive orbit videos of cellular reconstructions
- 📈 **Batch processing** for efficient analysis of multiple sperm cells
- 🔄 **Flexible file naming** that accommodates various naming conventions
- ✅ **Centralized configuration** with single source of truth for all parameters
- 🔎 **Tracking verification** with overlay images to ensure data quality before metrics

**Documentation Files:**
- [README.md](README.md) - This file, complete pipeline reference
- [FILE_NAMING_GUIDE.md](FILE_NAMING_GUIDE.md) - File naming conventions and flexible matching
- [TRACKING_OVERLAY_GUIDE.md](TRACKING_OVERLAY_GUIDE.md) - Comprehensive guide to verify tracking and debug metrics issues
- [TRACKMATE_CSV_FORMAT.md](TRACKMATE_CSV_FORMAT.md) - TrackMate CSV format reference
- [TRACKING_OVERLAY_QUICKREF.md](TRACKING_OVERLAY_QUICKREF.md) - One-page quick reference cheat sheet

---

## Table of Contents

1. [Biological Context](#biological-context)
2. [Preprocessing Pipeline](#preprocessing-pipeline)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [Architecture](#architecture)
6. [Usage Guide](#usage-guide)
7. [Output Description](#output-description)
8. [Metrics Reference](#metrics-reference)
9. [File Organization](#file-organization)
10. [Tracking Overlay Verification](#tracking-overlay-verification)
11. [Troubleshooting](#troubleshooting)
12. [Citation](#citation)

---

## Biological Context

This pipeline analyzes **sperm cells** and their subcellular structures (mitochondria, mitochondrial organelles, nucleus, pseudopod) to quantify morphological features relevant to cellular function and reproductive biology. Key biological measures include:

- **Distance to spermathecal valve**: Measures sperm positioning relative to the reproductive structure, indicating potential for successful fertilization
- **Pseudopod orientation**: Determines directional bias of the sperm tail toward or away from the spermathecal valve
- **Mitochondrial morphology**: Assesses fusion/fission status and metabolic capacity through shape metrics (sphericity, aspect ratio) and surface-area-to-volume ratios
- **Spatial organization**: Quantifies relationships between organelles (distances to nucleus, clustering) to understand cellular compartmentalization

The pipeline enables quantitative comparison of sperm morphology across samples, cell types, or treatment conditions.

---

## Preprocessing Pipeline

Each sperm cell undergoes extensive preprocessing before analysis:

### 1. **Sperm Cell Cropping & Segmentation**
- Individual sperm cells are cropped from large SEM image stacks
- Each cell assigned a unique numerical ID
- Multi-class image segmentation performed using a fine-tuned **Detectron2 model** (PyTorch-based instance segmentation)
- Model outputs predictions for: nucleus, pseudopod, mitochondria, mitochondrial organelles (MO), and sperm cell boundary
- Segmentations exported as binary mask TIFF stacks (one per organelle type, per sperm cell)

**Reference**: Detectron2 (https://github.com/facebookresearch/detectron2)

### 2. **Manual Mask Curation in ImageJ**
- All predicted binary masks manually reviewed for accuracy
- Corrections applied for low-quality predictions:
  - **Deletion**: Remove incorrectly detected structures
  - **Addition**: Add missed structures not detected by model
  - **Manipulation**: Adjust mask boundaries, fill holes, remove noise
- Ensures segmentations accurately reflect raw SEM images
- Corrected masks saved as cleaned binary TIFF stacks

**Tools**: ImageJ/Fiji image processing software

### 3. **Image Registration (stackreg)**
- **Problem**: SEM imaging ribbon often becomes compressed or warped during sectioning, causing localized image distortion that accumulates through the Z-stack
- **Solution**: Applied stackreg (Thévenaz 2024) for automatic image registration
- **Method**: Aligns each slice to a reference frame via:
  - Rotation optimization
  - X/Y translation (no scaling to preserve voxel dimensions)
  - Minimizes motion and drift artifacts within the stack
- **Output**: Registered TIFF stacks with consistent alignment across Z-slices
- **Naming convention**: Registered files marked with `_registration` suffix

**Reference**: 
- Thévenaz P, et al. (2024). "StackReg: An ImageJ plugin for the alignment of image sequences." 
- Original: Thévenaz P, et al. (1998). IEEE Trans Image Process. 7(1):27-41.

### 4. **Object Tracking (Mtrack2 Plugin)**
- **Purpose**: For organelles present in multiple copies (mitochondria, MO), individual tracking links each organelle across Z-slices
- **Tool**: MTrack2 plugin for ImageJ (Stuurman 2003)
- **Method**:
  - Plugin identifies particle centroids in each image slice
  - Links particles across consecutive frames (Z-slices) based on proximity
  - Assigns unique track ID to each organelle instance
- **Output**: Tracking table containing:
  - Frame number (Z-slice index)
  - X, Y centroid coordinates (in pixels)
  - Track ID (unique integer per organelle instance)
  - Additional columns (e.g., tracking confidence)
- **Scope**: Mitochondria and MO (multiple instances per cell)
- **Not tracked**: Nucleus, pseudopod, sperm cell (always single instance)

**Reference**: Stuurman N, et al. (2003). "Computer modeling of three-dimensional cell structures." J Struct Biol. 143(1):36-44.

### 5. **Data Assembly**
Processed data assembled into structured folders:
```
Sperm {ID}/
├── nucleus_stack_{ID}.tif                    (curated binary mask)
├── pseudopod_stack_{ID}.tif                  (curated binary mask)
├── sperm_cell_stack_{ID}.tif                 (curated binary mask)
├── mitochondria_stack_{ID}_registration.tif  (registered, curated)
├── mitochondria_stack_{ID}.tif               (unregistered, curated)
├── MO_stack_{ID}_registration.tif            (registered, curated)
├── MO_stack_{ID}.tif                         (unregistered, curated)
├── MO tracking/
│   └── {tracking_data}.csv                   (from Mtrack2)
└── Mito tracking/
    └── {tracking_data}.csv                   (from Mtrack2)
```

---

## Installation

### Requirements
- **Python**: 3.8 or higher
- **OS**: macOS, Linux, or Windows (with WSL)
- **RAM**: 8 GB minimum (16 GB recommended for batch processing)

### Step 1: Clone Repository
```bash
git clone https://github.com/yourusername/sperm-cell-analysis.git
cd sperm-cell-analysis
```

### Step 2: Create Virtual Environment (Recommended)
```bash
python -m venv env
source env/bin/activate  # macOS/Linux
# or
env\Scripts\activate  # Windows
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

**Key Dependencies:**
- `numpy`, `scipy`, `pandas`: Numerical computing
- `scikit-image`: Image processing and morphological analysis
- `opencv-python`: Image utilities
- `pyvista`: 3D visualization and mesh generation
- `imageio`: TIFF stack I/O
- `scikit-learn`: PCA for direction vector computation
- `read-roi`: ImageJ ROI file parsing
- `openpyxl`: Excel output

### Step 4: Configure Parameters (Optional)
Edit `src/config.py` to adjust analysis parameters:
```python
# Microscopy calibration
PIXEL_SIZE_UM = 0.008          # XY resolution (micrometers)
SLICE_THICKNESS_UM = 0.05      # Z resolution (micrometers)

# Segmentation
ORGANELLE_THRESHOLD = 128      # Binary threshold for masks

# 3D Mesh extraction
MESH_MIN_SIZE = 100            # Minimum voxels for objects
MESH_BLUR = 0.0                # Gaussian blur for smoothing

# Video rendering
VIDEO_NUM_FRAMES = 60          # Frames in 360° rotation
VIDEO_FPS = 10                 # Output video frame rate
```

See `src/config.py` for complete parameter list with documentation.

---

## Quick Start

### Analyze a Single Sperm Cell

```python
from src.utils import get_file_paths
from src.metrics import compute_organelle_metrics
from src.spatial_metrics import compute_spatial_metrics

# Define paths
sperm_id = 16
base_dir = "/path/to/Sperm_Cell_Data"

# Load file paths (automatically finds files)
file_paths = get_file_paths(sperm_id, base_dir, registered=True)

# Compute organelle metrics
pseudopod_centroid = get_centroid(file_paths["pseudopod"])
nucleus_centroid = get_centroid(file_paths["nucleus"])

organelle_inputs = [
    ("mitochondria", file_paths["mitochondria"], file_paths.get("mito_csv")),
    ("MO", file_paths["MO"], file_paths.get("mo_csv")),
    ("pseudopod", file_paths["pseudopod"], None),
    ("nucleus", file_paths["nucleus"], None),
    ("sperm_cell", file_paths["sperm_cell"], None),
]

all_metrics = []
for org_name, stack_path, csv_path in organelle_inputs:
    df = compute_organelle_metrics(
        org_name, stack_path, csv_path,
        pseudopod_centroid, nucleus_centroid, f"sperm_{sperm_id}"
    )
    all_metrics.append(df)

metrics_df = pd.concat(all_metrics, ignore_index=True)
```

### Run Full Jupyter Notebook
Start the interactive pipeline:
```bash
jupyter notebook Sperm_Cell_Analysis_Pipeline.ipynb
```

Then follow the step-by-step instructions in the notebook.

---

## Architecture

### Project Structure

```
sperm-cell-analysis/
├── src/                                    # Core analysis modules
│   ├── config.py                          # Configuration parameters
│   ├── utils.py                           # Utility functions (file I/O, voxel conversion)
│   ├── analysis_utils.py                  # Data loading and preprocessing
│   ├── metrics.py                         # Organelle metrics computation
│   ├── spatial_metrics.py                 # Distance-to-valve calculations
│   ├── tracking.py                        # Mtrack2 CSV parsing and conversion
│   ├── reconstruction.py                  # 3D mesh generation and visualization
│   └── detectron_inference.py             # Detectron2 segmentation (if used)
├── Sperm_Cell_Analysis_Pipeline.ipynb     # Main interactive analysis notebook
├── Convert tracking and visualize.py      # Standalone tracking conversion script
├── requirements.txt                       # Python dependencies
├── README.md                              # This file
└── outputs/
    └── Sperm_{ID}/                        # Analysis results per sperm cell
        ├── Organellar_Measures/           # Metrics CSV files
        ├── spatial_metrics.xlsx           # Distance/angle analysis
        └── Sperm_{ID}_rotation.gif        # 3D visualization
```

### Module Overview

#### `src/config.py`
**Purpose**: Centralized configuration for microscopy calibration and algorithm parameters.

**Key Parameters**:
- `PIXEL_SIZE_UM`: XY resolution (default: 0.008 µm)
- `SLICE_THICKNESS_UM`: Z-axis resolution (default: 0.05 µm)
- `VIDEO_NUM_FRAMES`: Number of frames in 360° rotation (default: 60)
- `MESH_MIN_SIZE`: Minimum object size in voxels (default: 100)

#### `src/utils.py`
**Purpose**: File I/O, coordinate system conversion, and general utilities.

**Key Functions**:
- `get_file_paths(sperm_id, base_dir, registered=True)`: Locates all TIFF stacks and tracking CSVs
- `load_tiff_stack(filepath)`: Loads TIFF files into numpy arrays
- `save_excel(df, filepath)`: Exports DataFrames to Excel with formatting
- `voxels_to_micrometers(coords)`: Converts voxel coordinates to physical units
- `get_centroid(stack)`: Computes 3D centroid from binary mask

#### `src/analysis_utils.py`
**Purpose**: Data loading, preprocessing, and TIFF stack utilities.

**Key Functions**:
- `get_centroid_from_roi(roi_path)`: Loads ImageJ ROI files
- `load_organelle_stack(filepath, preprocess=False)`: Loads stacks with optional filtering
- `load_tracking_data(csv_path)`: Reads Mtrack2 CSV output

#### `src/metrics.py`
**Purpose**: Computes morphological metrics for all organelles.

**Key Functions**:
- `compute_organelle_metrics()`: Main metric computation function
  - Inputs: Organelle name, TIFF path, optional tracking CSV
  - Outputs: DataFrame with 13 columns (volume, surface area, sphericity, centroid, distances, etc.)
- `get_volume_surface_from_labeled_volume()`: Computes volume and surface area using marching cubes
- `calculate_sphericity()`: Measures sphericity (0=elongated, 1=perfect sphere)
- `get_aspect_ratio()`: Computes aspect ratio from principal component analysis

**Algorithm**:
1. Load binary TIFF stack
2. If tracking CSV provided: Process each tracked instance separately
3. Extract 3D connected components
4. For each component, compute:
   - Volume (sum of voxels × voxel volume)
   - Surface area (marching cubes algorithm)
   - Sphericity, aspect ratio, bounding box
   - Centroid (center of mass)
   - Euclidean distances to pseudopod and nucleus centroids
5. Return metrics DataFrame

#### `src/spatial_metrics.py`
**Purpose**: Computes spatial relationships between sperm cell and spermathecal valve.

**Key Functions**:
- `compute_spatial_metrics()`: Calculates distance from sperm to valve
  - Inputs: Sperm centroid, pseudopod tip, valve location
  - Outputs: Distances and angles in physical units

**Metric Definitions**:
- **Distance to Valve (Centroid)**: Euclidean distance from sperm cell center to valve
- **Distance to Valve (Pseudopod Tip)**: Euclidean distance from pseudopod terminus to valve
- **Angle to Valve**: Angle between pseudopod direction vector and vector pointing to valve

#### `src/tracking.py`
**Purpose**: Parses Mtrack2 CSV output and converts to usable format.

**Key Functions**:
- `parse_mtrack2_csv(csv_path)`: Reads Mtrack2 output
- `get_tracking_df(csv_path)`: Returns tracking as pandas DataFrame with columns:
  - `Frame`: Z-slice index
  - `X`, `Y`: Centroid coordinates
  - `Track_ID`: Unique organelle ID

**Note**: Mtrack2 is an external ImageJ plugin. CSV files are manually generated before Python analysis.

#### `src/reconstruction.py`
**Purpose**: 3D mesh generation and volumetric visualization.

**Key Functions**:
- `create_3d_mesh_pyvista()`: Generates mesh from binary stack
  - Uses marching cubes algorithm
  - Extracts surface from volumetric data
- `plot_3d_rotation()`: Creates rotating visualization
  - Generates 60-frame orbit animation
  - Outputs as GIF for presentation

**Algorithm**:
1. Load binary TIFF stack (voxelated representation)
2. Apply marching cubes to extract iso-surface at threshold=0.5
3. Simplify mesh if needed
4. Create PyVista scene with lighting
5. Render 60 frames at different angles (0° to 360°)
6. Save as animated GIF

### Data Flow Diagram

```
Raw TIFF Stacks (ImageJ)
     ↓
[Binary Masks + Tracking CSVs]
     ↓
     ├─→ src/metrics.py ─→ Volume, Surface Area, Sphericity
     │   [compute_organelle_metrics()]
     │
     ├─→ src/spatial_metrics.py ─→ Distance to Valve
     │   [compute_spatial_metrics()]
     │
     └─→ src/reconstruction.py ─→ 3D Mesh → Rotation Video
        [create_3d_mesh_pyvista(), plot_3d_rotation()]
     ↓
 Pandas DataFrame (metrics)
     ↓
Excel/CSV Output
```

### Key Algorithms

#### 1. **Volume and Surface Area Computation**
**Algorithm**: Marching Cubes (Lorensen & Cline 1987)

**Input**: 3D binary array (voxelated organelle)

**Process**:
1. Interpolate binary voxel grid
2. Find isosurface at threshold 0.5
3. Generate triangle mesh at surface boundary
4. Calculate volume as sum of filled voxels × voxel volume
5. Calculate surface area from triangle mesh

**Output**: Volume (µm³), Surface Area (µm²)

#### 2. **Sphericity Calculation**
**Formula**: $S = \frac{\pi^{1/3} (3V)^{2/3}}{A}$

Where:
- $V$ = Volume
- $A$ = Surface area
- $S$ = Sphericity (0-1, 1 = perfect sphere)

**Interpretation**:
- 0.9-1.0: Nearly spherical
- 0.7-0.9: Moderately elongated
- <0.7: Highly elongated

#### 3. **Principal Component Analysis (Direction Vector)**
**Algorithm**: Eigenvalue decomposition of covariance matrix

**Input**: Set of voxel coordinates for organelle

**Process**:
1. Compute centroid $(x_0, y_0, z_0)$
2. Center coordinates: $X_i = x_i - x_0$, etc.
3. Compute covariance matrix: $\Sigma = \frac{1}{N} X^T X$
4. Eigendecomposition: $\Sigma = U \Lambda U^T$
5. First eigenvector (largest eigenvalue) = primary direction

**Output**: Direction vector (unit vector) indicating elongation orientation

#### 4. **Distance Calculation**
**Formula**: Euclidean distance

$$d = \sqrt{(x_1-x_2)^2 + (y_1-y_2)^2 + (z_1-z_2)^2}$$

**Conversion**: Voxel distance → Physical distance (multiply by voxel size)

### Processing Pipeline (Detailed)

1. **Load Data**
   - Read TIFF stacks (binary masks)
   - Load tracking CSVs (if available)
   - Extract centroid locations

2. **Single Organelle Processing**
   - Get connected components (scipy.ndimage.label)
   - For each component:
     - Measure volume, surface area
     - Calculate sphericity, aspect ratio
     - Compute centroid

3. **Multiple Organelle Processing (Tracked)**
   - Parse tracking CSV
   - For each frame (Z-slice):
     - Associate pixels with Track_ID
     - Compute metrics per tracked instance

4. **Spatial Analysis**
   - Register sperm cell centroid (0, 0, 0) in local coordinates
   - Locate pseudopod tip from principal component
   - Calculate distances to reference point (valve location)
   - Compute angle between pseudopod direction and valve direction

5. **3D Visualization**
   - Extract isosurface using marching cubes
   - Create triangle mesh
   - Render 60 frames at different rotation angles
   - Save as GIF

### Coordinate Systems

**Image Coordinates** (TIFF stacks):
- Origin: (0, 0, 0) at top-left-front
- Units: Pixels/voxels
- Axes: X (left-right), Y (up-down), Z (front-back)

**Physical Coordinates** (outputs):
- Units: Micrometers (µm)
- Conversion: `physical = voxel × voxel_size`
- Default: PIXEL_SIZE_UM = 0.008 µm, SLICE_THICKNESS_UM = 0.05 µm

**Local Coordinates** (spatial metrics):
- Origin: Sperm cell centroid
- Units: Micrometers
- Used for distance calculations

---

## Usage Guide

The pipeline provides three main workflows:

### Workflow 1: Single-Cell Analysis
**Use when**: Analyzing one sperm cell in detail with optional visualization.

**Steps**:
1. Configure `sperm_id` and `base_dir` in notebook
2. Run Step 2a: Tracking conversions (if using Mtrack2 CSVs)
3. Run Step 2b: Compute organelle metrics
4. Run Step 2c: Compute spatial metrics (distance to spermathecal valve)
5. Run Step 2d: Build 3D reconstruction with orbit video

**Time**: ~5-10 minutes per cell

**Outputs**:
- `Sperm {ID}/Organellar_Measures/{sample_id}_all_metrics.csv`
- `Sperm {ID}/spatial_metrics.xlsx`
- `Sperm {ID}/Sperm_{ID}_rotation.gif`

### Workflow 2: Batch Processing
**Use when**: Analyzing multiple sperm cells (10+) for statistical comparison.

**Steps**:
1. Edit `sperm_ids_to_process` list in Step 3 of notebook
2. Run batch processing cell
3. Results compiled into single Excel file

**Time**: ~2-3 minutes per cell

**Output**:
- `batch_results_all_cells/all_metrics_batch.xlsx` (all cells + metrics combined)

### Workflow 3: Unfused MO Analysis (Optional)
**Use when**: Analyzing unfused mitochondrial organelle (MO) data separately.

**Steps**:
1. Specify which sperm cells have unfused MO data in Step 4
2. Run unfused MO analysis
3. Results saved to dedicated Excel file

**Time**: ~1-2 minutes per cell

**Outputs**:
- `unfused_mo_metrics.xlsx`
- `unfused_mo_run_report.csv` (processing status)

---

## Output Description

### Organelle Metrics CSV
**File**: `{sample_id}_all_metrics.csv`

**Columns**:
| Column | Description | Units |
|--------|-------------|-------|
| Sample_ID | Unique sperm cell identifier | - |
| Organelle_Type | Type of organelle (nucleus, pseudopod, mitochondria, MO, sperm_cell) | - |
| Track_ID | Unique ID for each organelle instance (varies for multiple organelles) | - |
| Volume_µm3 | Organelle volume | cubic micrometers |
| Surface_Area_µm2 | Organelle surface area | square micrometers |
| Sphericity | Measure of how spherical the organelle is (0-1, 1=perfect sphere) | - |
| Centroid_z, _y, _x | 3D location of organelle center | voxels (convert to µm with VOXEL_SIZE) |
| Distance_to_Pseudopod | Euclidean distance from organelle to pseudopod centroid | voxels |
| Distance_to_Nucleus | Euclidean distance from organelle to nucleus centroid | voxels |
| BoundingBox_Volume_µm3 | Volume of smallest box containing organelle | cubic micrometers |
| Density | Ratio of organelle volume to bounding box volume (0-1) | - |
| Aspect_Ratio | Ratio of longest to shortest dimension (≥1) | - |
| Direction_Vector_z, _y, _x | Principal component direction (pseudopod only) | - |

**Note**: For multiple organelles (mitochondria, MO), one row per organelle instance. For single organelles, one row per sperm cell.

### Spatial Metrics Excel
**File**: `spatial_metrics.xlsx`

**Columns**:
| Column | Description | Units |
|--------|-------------|-------|
| centroid_global | Sperm cell centroid in global image space | voxels |
| pseudopod_tip_global | Tip of pseudopod in global image space | voxels |
| distance_centroid_to_target_um | Distance from sperm centroid to spermathecal valve | micrometers |
| distance_pseudopod_tip_to_target_um | Distance from pseudopod tip to spermathecal valve | micrometers |
| angle_between_direction_and_target_vector_deg | Angle between pseudopod orientation and direction toward valve | degrees |

**Interpretation**:
- **Small centroid distance**: Sperm cell positioned close to spermathecal valve
- **Small angle (0°)**: Pseudopod oriented directly toward valve (favorable for fertilization)
- **Large angle (180°)**: Pseudopod oriented away from valve (unfavorable positioning)

### 3D Reconstruction Video
**File**: `Sperm_{ID}_rotation.gif`

**Content**: Animated 360° orbit view showing all organelles with colors:
- 🟢 Green: Sperm cell boundary (translucent)
- 🟤 Brown/Dark Green: Pseudopod
- ⚫ Black: Nucleus
- 🟠 Orange: Mitochondria
- 🟣 Purple: Mitochondrial organelles (MO)

---

## Metrics Reference

### Volume
**Definition**: Total voxel count × voxel volume

**Formula**:
```
Volume (µm³) = Number_of_Voxels × (PIXEL_SIZE_UM² × SLICE_THICKNESS_UM)
```

**Biological significance**: Indicates organelle size and metabolic capacity.

### Surface Area
**Definition**: Computed via marching cubes algorithm, then mesh surface area calculation.

**Biological significance**: Combined with volume (see SA:V ratio below), indicates surface-to-volume efficiency.

### Sphericity
**Definition**: Measure of how close an object is to a perfect sphere.

**Formula**:
```
Sphericity = (π^(1/3) × (6V)^(2/3)) / A

Where:
  V = Volume (µm³)
  A = Surface Area (µm²)
  π^(1/3) ≈ 1.612
```

**Range**: 0 to 1
- 1.0 = Perfect sphere
- 0.5 = Rod-like structure
- Values < 0.5 = Highly elongated or irregular

**Biological significance**: Abnormally shaped mitochondria (low sphericity) indicate fusion events or incomplete fission.

**Reference**: Hammerquist et al. (2021). Mitochondrial morphology as indicator of metabolic state.

### Surface Area-to-Volume Ratio (SA:V)
**Definition**: Surface area divided by volume.

**Biological significance**: Indicates capacity for molecular exchange with environment:
- **High SA:V**: Greater surface for nutrient uptake and waste removal → increased metabolic efficiency
- **Low SA:V**: Less surface area → potentially reduced metabolic efficiency

**Interpretation**: Spherical mitochondria have higher SA:V than elongated ones with same volume.

### Aspect Ratio
**Definition**: Ratio of longest to shortest dimension in bounding box.

**Formula**:
```
Aspect_Ratio = max(depth, width, height) / min(depth, width, height)
```

**Range**: ≥ 1.0
- 1.0 = Cube (equal dimensions)
- > 2.0 = Highly elongated structure
- Very high (>10) = Rod or tubular structure

**Biological significance**: Indicates mitochondrial shape changes:
- High aspect ratio (>3): Tubular, networked mitochondria
- Low aspect ratio (≈1): Fragmented, round mitochondria (indicates fission)

### Density
**Definition**: Ratio of object volume to bounding box volume.

**Formula**:
```
Density = Organelle_Volume / BoundingBox_Volume
```

**Range**: 0 to 1
- 1.0 = Object perfectly fills bounding box (compact)
- 0.5 = Object fills 50% of bounding box (loose/sparse)

**Biological significance**: Indicates structural compactness and presence of internal voids.

### Direction Vector (Pseudopod Only)
**Definition**: Principal component from PCA analysis of pseudopod voxel coordinates.

**Method**:
1. Extract all voxels in pseudopod 3D binary mask
2. Apply PCA to compute principal axes
3. First principal component = elongation direction

**Biological significance**: Indicates pseudopod orientation in 3D space:
- Used to calculate angle toward spermathecal valve
- Reveals if sperm is "aimed" toward fertilization site
- 0° = pseudopod pointing directly at valve (favorable)
- 180° = pseudopod pointing away (unfavorable)

### Distances to Reference Structures
**Definition**: Euclidean distance between organelle centroid and reference point.

**Calculation**:
```
Distance = √[(x₁-x₂)² + (y₁-y₂)² + (z₁-z₂)²] × VOXEL_SIZE
```

**Reference points**:
- **Nucleus centroid**: Center of nucleus organelle
- **Pseudopod centroid**: Center of pseudopod structure
- **Spermathecal valve**: User-defined reference point (spermathecal valve center in global image space)

---

## File Organization

The pipeline uses **flexible file naming** to accommodate various naming schemes. **See [FILE_NAMING_GUIDE.md](FILE_NAMING_GUIDE.md) for complete specifications.**

Quick summary:
- **Single organelles** (nucleus, pseudopod, sperm_cell): Always unregistered
- **Multiple organelles** (mitochondria, MO): Have both registered (for tracking) and unregistered (for 3D) versions
- **Flexible naming**: Case-insensitive, spacing flexible, "stack" keyword optional
- **STRICT**: `_registration` suffix determines which version is used

### Directory Structure
```
Project Root/
├── README.md                              (this file)
├── FILE_NAMING_GUIDE.md                   (naming conventions)
├── requirements.txt                        (Python dependencies)
├── Sperm_Cell_Analysis_Pipeline.ipynb     (main analysis notebook)
│
├── src/
│   ├── __init__.py
│   ├── config.py                          (centralized parameters)
│   ├── utils.py                           (file discovery, utilities)
│   ├── metrics.py                         (organelle metrics computation)
│   ├── spatial_metrics.py                 (spatial analysis)
│   ├── tracking.py                        (tracking CSV processing)
│   ├── reconstruction.py                  (3D mesh & visualization)
│   ├── detectron_inference.py            (model inference helpers)
│   └── analysis_utils.py                  (analysis utilities)
│
├── Sample Data/
│   └── Sperm {ID}/
│       ├── nucleus_stack_{ID}.tif
│       ├── pseudopod_stack_{ID}.tif
│       ├── sperm_cell_stack_{ID}.tif
│       ├── mitochondria_stack_{ID}_registration.tif
│       ├── mitochondria_stack_{ID}.tif
│       ├── MO_stack_{ID}_registration.tif
│       ├── MO_stack_{ID}.tif
│       ├── MO tracking/
│       │   ├── {tracking_data}.csv
│       │   └── tracking_overlays/
│       │       └── {organelle}_overlays/
│       │           └── frame_001_overlay.png (tracking verification images)
│       ├── Mito tracking/
│       │   ├── {tracking_data}.csv
│       │   └── tracking_overlays/
│       │       └── {organelle}_overlays/
│       │           └── frame_001_overlay.png (tracking verification images)
│       └── Organellar_Measures/
│           └── sperm_{ID}_all_metrics.csv
│
└── outputs/
    ├── batch_results_all_cells/
    │   └── all_metrics_batch.xlsx
    └── Sperm {ID}/
        ├── spatial_metrics.xlsx
        └── Sperm_{ID}_rotation.gif
```

---

## Tracking Overlay Verification

### Quick Summary

**Purpose**: Visually verify that the automatic tracking system correctly linked organelles across image slices before running metrics analysis.

**Key Point**: If metrics look wrong for mitochondria (Mito) or MO, **check overlays first** — 90% of the time the problem is in tracking, not the metrics code.

### How to Generate Overlays

**In Notebook (Easiest)**:
Step 2e in `Sperm_Cell_Analysis_Pipeline.ipynb` generates overlays automatically.

**Programmatically**:
```python
from src.tracking import visualize_tracking

overlay_dir = visualize_tracking(
    tiff_path="Sperm 14/mitochondria_stack_14_registration.tif",
    csv_path="Sperm 14/Mito tracking/tracking.csv",
    frames_to_display=200,
    save_overlays=True
)
```

### What to Look For

**✅ Good Tracking**:
- Red circles with track IDs visible in most frames
- Same ID stays consistent across frames (track #5 is always #5)
- Smooth motion, no jumping
- ~Constant organelle population

**🚨 Bad Tracking**:
- Many white circles but few/no red circles (no IDs)
- IDs suddenly change or disappear
- Circles jump erratically
- Population varies wildly

### Troubleshooting Tracking Issues

**Problem: Metrics seem unrealistic (e.g., volume = 0, distances = NaN)**

1. Generate overlays for the affected cell
2. Scan through frames looking for tracking failures
3. Use the **decision tree** in [TRACKING_OVERLAY_GUIDE.md](TRACKING_OVERLAY_GUIDE.md) to diagnose:
   - **Few/no track IDs** → Check segmentation or detection threshold
   - **Erratic circle motion** → Check registration (SEM image jumping)
   - **ID keeps changing** → Check linking distance parameter
   - **Blank frames** → Check original TIFF quality
4. Fix the root cause (re-register, adjust threshold, etc.)
5. Re-run metrics for that cell

### Where Overlays Are Stored

```
Sperm {ID}/
├── Mito tracking/tracking_overlays/mitochondria_overlays/frame_XXX_overlay.png
└── MO tracking/tracking_overlays/MO_overlays/frame_XXX_overlay.png
```

**→ See [TRACKING_OVERLAY_GUIDE.md](TRACKING_OVERLAY_GUIDE.md) for complete troubleshooting workflow and visual examples.

---

## Troubleshooting

### "No [organelle] file found" Error
**Cause**: File naming doesn't match expected pattern.

**Solutions**:
1. Check file exists in correct directory: `Sperm {ID}/`
2. Verify correct file extension (`.tif`, not `.tiff` or `.TIF`)
3. Review [FILE_NAMING_GUIDE.md](FILE_NAMING_GUIDE.md) for acceptable patterns
4. Check that organelle name matches expected names (nucleus, pseudopod, mitochondria, MO, sperm_cell)

### "Multiple files found" Warning
**Cause**: Duplicate files in directory matching same pattern.

**Solution**: Remove duplicate files or rename to distinguish them.

### Tracking CSV Not Found
**Cause**: CSV naming doesn't match flexible patterns.

**Expected patterns**:
- `MO_tracking_16.csv` or `MO_tracking_16.csv` or `tracking_MO_16.csv`
- `mitochondria_tracking_16.csv` or `Mito_tracking_16.csv`

**Solution**: Rename CSV to match one of these patterns or check [FILE_NAMING_GUIDE.md](FILE_NAMING_GUIDE.md).

### 3D Reconstruction Appears Distorted
**Cause**: Using unregistered images for reconstruction (registered images have corrected distortions that don't match actual voxel positions).

**Solution**: Ensure 3D reconstruction uses **unregistered** TIFF files (no `_registration` suffix).

### Memory Issues During Batch Processing
**Cause**: Processing very large TIFF stacks (>200 MB each).

**Solutions**:
1. Process fewer cells per batch (reduce `sperm_ids_to_process` list size)
2. Pre-downscale TIFF stacks using ImageJ
3. Increase available RAM or close other applications
4. Process cells individually instead of batch

### Voxel Size Mismatch
**Cause**: Using different voxel sizes in different modules.

**Solution**: All voxel sizes defined in `src/config.py`. Verify values match your microscopy calibration:
```python
PIXEL_SIZE_UM = 0.008      # Your pixel size in micrometers
SLICE_THICKNESS_UM = 0.05  # Your Z resolution in micrometers
```

### Sphericity Calculation Errors
**Cause**: Marching cubes fails on organelles with too few voxels.

**Solution**: Increase `ORGANELLE_THRESHOLD` in `src/config.py` to segment only robust structures, or manually review masks in ImageJ.

### Unexpected Metrics for Mitochondria or MO

**First, always check tracking overlays:**

```python
# Generate overlays to verify tracking quality
from src.tracking import visualize_tracking

overlay_dir = visualize_tracking(
    tiff_path="path/to/{organelle}_stack_{ID}_registration.tif",
    csv_path="path/to/Sperm {ID}/{Organelle} tracking/tracking.csv",
    frames_to_display=200,
    save_overlays=True
)

print(f"View overlays at: {overlay_dir}")
```

**Common causes of bad metrics:**

1. **Tracking failures** (see [Tracking Overlay Verification](#tracking-overlay-verification))
   - Missing track IDs in some frames
   - ID jumps or resets between frames
   - Organelles not being detected at all
   - **Solution**: Review overlay images; if tracking is bad, fix segmentation or registration and re-run

2. **Segmentation artifacts**
   - Holes or gaps in organelle masks
   - Over-segmentation (mask too large)
   - Under-segmentation (mask too small)
   - **Solution**: Review masks in ImageJ and manually correct

3. **Registration problems**
   - Artifacts from stackreg that affect downstream analysis
   - **Solution**: Check both registered and unregistered TIFF files; may need to re-register with different parameters

4. **Threshold issues**
   - Organelles too small to process (volume = 0)
   - **Solution**: Lower `MESH_MIN_SIZE` threshold in `src/config.py`

**Debugging workflow:**
1. Generate tracking overlays for the problematic cell
2. Review overlay images for tracking failures (see [Interpreting Overlays](#interpreting-overlays))
3. If tracking looks good → problem is in segmentation or registration
4. If tracking looks bad → fix tracking and re-generate overlays
5. Re-run metrics after fix

---

## Citation

If you use this pipeline in your research, please cite:

```bibtex
@software{sperm_cell_analysis_2024,
  author = {Rothman, Arielle},
  title = {Sperm Cell 3D Morphometric Analysis Pipeline},
  year = {2024},
  url = {https://github.com/yourusername/sperm-cell-analysis},
  note = {Python pipeline for quantitative analysis of sperm morphology from SEM image stacks}
}
```

### Related Publications
- Thévenaz P, et al. (2024). "StackReg: An ImageJ plugin for the alignment of image sequences."
- Stuurman N, et al. (2003). "Computer modeling of three-dimensional cell structures." *J Struct Biol* 143(1):36-44.
- Hammerquist et al. (2021). "Mitochondrial morphology as indicator of metabolic state."

---

## License

This project is licensed under the [MIT License](LICENSE) - see LICENSE file for details.

---

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit changes (`git commit -am 'Add your feature'`)
4. Push to branch (`git push origin feature/your-feature`)
5. Open a pull request

---

## Contact & Support

For questions, issues, or suggestions:
- Open an issue on GitHub
- Contact: [your email]
- Institution: [your institution]

---

## Acknowledgments

This pipeline builds on the ImageJ ecosystem and several key open-source projects:
- **Detectron2**: Instance segmentation framework
- **scikit-image**: Image processing algorithms
- **PyVista**: 3D visualization
- **ImageJ/Fiji**: Image analysis and preprocessing
- **stackreg**: Image registration
- **Mtrack2**: Particle tracking in ImageJ

---

**Last Updated**: January 2024  
**Version**: 1.0.0  
**Status**: Production-ready for thesis publication
