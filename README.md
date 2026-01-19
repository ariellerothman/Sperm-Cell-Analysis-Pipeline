# Sperm Cell 3D Morphometric Analysis Pipeline

Automated 3D morphometric analysis of sperm cells from SEM image stacks. This pipeline processes binary segmentation masks (derived from Detectron2 predictions or manual segmentation), tracking data, and microscopy calibration to compute detailed cellular and organellar metrics. Enables quantitative assessment of sperm cell morphology, spatial organization, and organellar relationships through 3D reconstruction and morphological analysis.

**Key Features:**
- **Multi-organelle analysis** with automatic single vs. multiple instance detection
- **Comprehensive metrics** including volume, surface area, sphericity, density, and spatial relationships
- **3D visualization** with interactive orbit videos of cellular reconstructions
- **Batch processing** for efficient analysis of multiple sperm cells
- **Flexible file naming** that accommodates various naming conventions
- **Centralized configuration** with single source of truth for all parameters
- **Tracking verification** with overlay images to ensure data quality before metrics
- **Optional Detectron2 integration** for automated mask generation from raw SEM images

**Documentation Files:**
- [README.md](README.md) - Main reference (this file)
- [QUICK_START.md](QUICK_START.md) - Get running in 5 minutes
- [FILE_NAMING_GUIDE.md](FILE_NAMING_GUIDE.md) - File naming conventions
- [METRICS_REFERENCE.md](METRICS_REFERENCE.md) - Detailed metric definitions and formulas
- [TRACKING_OVERLAY_GUIDE.md](TRACKING_OVERLAY_GUIDE.md) - Tracking verification guide
- [TRACKING_OVERLAY_QUICKREF.md](TRACKING_OVERLAY_QUICKREF.md) - One-page tracking quick reference
- [Detectron2_Mask_Generation_Colab.ipynb](Detectron2_Mask_Generation_Colab.ipynb) - Automated mask generation template

---

## Table of Contents

1. [Biological Context](#biological-context)
2. [Quick Start](#quick-start)
3. [Detectron2 Mask Generation](#detectron2-mask-generation-optional)
4. [Installation](#installation)
5. [Architecture](#architecture)
6. [Usage Guide](#usage-guide)
7. [Output Description](#output-description)
8. [Troubleshooting](#troubleshooting)
9. [Citation](#citation)

---

## Preprocessing Pipeline

Each sperm cell undergoes extensive preprocessing before analysis:

### 1. **Sperm Cell Cropping & Segmentation**
- Individual sperm cells are cropped from large SEM image stacks
- Each cell assigned a unique numerical ID
- Multi-class image segmentation performed using a fine-tuned **Detectron2 model** (PyTorch-based instance segmentation)
- Model outputs predictions for: nucleus, pseudopod, mitochondria, membranous organelles (MO), and sperm cell boundary
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
├── MO_tracking_{ID}.csv                      (from Mtrack2)
├── Mito_Tracking_{ID}.csv                    (from Mtrack2)

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

### Option 1: Analyze Pre-Generated Masks

If you already have binary segmentation masks (from Detectron2 or manual segmentation):

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

### Option 2: Generate Masks with Detectron2 (Optional)

See [Detectron2 Mask Generation Guide](#detectron2-mask-generation-optional) below.

### Option 3: Run Full Interactive Pipeline
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
│   ├── utils.py                           # Utility functions (file I/O, voxel conversion, data loading)
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
- `find_file_by_pattern(folder, organelle, sperm_id, registered, exclude_pattern)`: Finds TIFF files with flexible naming conventions
- `find_csv_by_pattern(folder, organelle, sperm_id)`: Finds tracking CSV files

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

### Processing Pipeline (Detailed)

1. **Load Data**
   - Read TIFF stacks (binary masks)
   - Load tracking CSVs 

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

---

## Detectron2 Mask Generation (Optional)

### Overview

This pipeline can work with binary segmentation masks from manual segmentation or deep learning. However, we provide a **Detectron2-based instance segmentation model** trained on sperm cell SEM images for automated mask generation.

**Key Features:**
-  **Instance segmentation**: Separately identifies individual organelles
-  **Multi-class prediction**: Nucleus, pseudopod, mitochondria, MO, sperm cell, unfusedMO
-  **Colab-based**: Free GPU access, no local hardware required
-  **High accuracy**: Trained on manually curated SEM image stacks

### Getting Started with Colab

1. **Open the template notebook:**
   - [Detectron2_Mask_Generation_Colab.ipynb](Detectron2_Mask_Generation_Colab.ipynb) (in this repository)
   - Or open it directly in Colab: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ariellerothman/sperm-cell-analysis/blob/main/Detectron2_Mask_Generation_Colab.ipynb)

2. **Request Model Weights:**
   - Email: [your email] with subject "Sperm Cell Detectron2 Model Request"
   - Include: Brief description of your use case
   - We'll provide download instructions for the trained model weights

3. **Generate Masks:**
   - Update paths in the Colab notebook
   - Run all cells
   - Download generated mask stacks from Google Drive
   - Use them with the main analysis pipeline

### Detectron2 Workflow

```
Raw SEM Images (TIFF stack)
        ↓
[Detectron2 in Colab]
        ↓
Binary Mask Stacks (.tif)
        ↓
[Sperm Cell Analysis Pipeline]
        ↓
Metrics & 3D Reconstruction
```

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
**Use when**: Analyzing unfused membranous organelle (MO) data separately.

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
| sample_id | Unique sperm cell identifier | - |
| organelle_type | Type of organelle (nucleus, pseudopod, mitochondria, mo, sperm_cell) | - |
| track_id | Unique ID for each organelle instance (varies for multiple organelles) | - |
| volume_um3 | Organelle volume | cubic micrometers |
| surface_area_um2 | Organelle surface area | square micrometers |
| sphericity | Measure of how spherical the organelle is (0-1, 1=perfect sphere) | - |
| centroid_z, _y, _x | 3D location of organelle center | voxels (convert to µm with voxel_size) |
| distance_to_pseudopod | Euclidean distance from organelle to pseudopod centroid | voxels |
| distance_to_nucleus | Euclidean distance from organelle to nucleus centroid | voxels |
| bounding_box_volume_um3 | Volume of smallest box containing organelle | cubic micrometers |
| density | Ratio of organelle volume to bounding box volume (0-1) | - |
| aspect_ratio | Ratio of longest to shortest dimension (≥1) | - |
| direction_vector_z, _y, _x | Principal component direction (pseudopod only) | - |

**Note**: For multiple organelles (mitochondria, mo), one row per organelle instance. For single organelles, one row per sperm cell.

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

---

## File Organization

**See [FILE_NAMING_GUIDE.md](FILE_NAMING_GUIDE.md) for complete file naming conventions and directory structure specifications.**

---

### Related Publications
- Thévenaz P, et al. (2024). "StackReg: An ImageJ plugin for the alignment of image sequences."
- Stuurman N, et al. (2003). "Computer modeling of three-dimensional cell structures." *J Struct Biol* 143(1):36-44.
- Hammerquist et al. (2021). "Mitochondrial morphology as indicator of metabolic state."

---

## License

This project is licensed under the [MIT License](LICENSE) - see LICENSE file for details.

---

## Contact & Support

For questions, issues, or suggestions:
- Open an issue on GitHub
- Contact: arielle.rothman@mail.utoronto.ca
- Institution: University of Toronto

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
