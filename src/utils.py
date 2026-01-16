import os
import glob
import numpy as np
from skimage import io, measure
from skimage.transform import resize

def downscale_3d(arr, scale=0.5):
    new_shape = tuple([int(s * scale) for s in arr.shape])
    arr_down = resize(arr, new_shape, order=1, preserve_range=True, anti_aliasing=True).astype(arr.dtype)
    return arr_down

def find_file_by_pattern(folder: str, organelle: str, sperm_id: int, registered: bool = False, exclude_pattern: str = None) -> str:
    """Find organelle TIFF file with flexible naming conventions.
    
    Handles variations in file naming:
    - Case insensitivity: 'nucleus', 'Nucleus', 'NUCLEUS'
    - Spacing variations: 'sperm cell', 'sperm_cell', 'spermcell'
    - Optional 'stack' keyword: 'nucleus_stack_16.tif' or 'nucleus_16.tif'
    - Registration suffix: '_registration' appears only in registered versions
    - Exclusion patterns: Can exclude files matching certain patterns (e.g., "unfused")
    
    Args:
        folder: Folder containing TIFF files (e.g., '/path/Sperm 16/')
        organelle: Organelle name (e.g., 'nucleus', 'mitochondria', 'MO')
        sperm_id: Sperm cell ID number
        registered: If True, finds registered version (_registration suffix).
                   If False, excludes registered versions.
        exclude_pattern: Optional pattern to exclude from matches (e.g., "unfused" to skip unfused MO).
    
    Returns:
        Full path to matching TIFF file.
    
    Raises:
        FileNotFoundError: If no matching file found.
    """
    # Find all TIFF files in folder and match case-insensitively
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"Folder not found: {folder}")
    
    all_tiffs = [f for f in os.listdir(folder) if f.lower().endswith('.tif')]
    
    # Normalize search terms for case-insensitive matching
    org_lower = organelle.lower()
    sperm_id_str = str(sperm_id)
    exclude_lower = exclude_pattern.lower() if exclude_pattern else None
    
    # Find matches: must contain organelle name and sperm_id (case-insensitive)
    candidates = []
    for tiff_file in all_tiffs:
        fname_lower = tiff_file.lower()
        
        # Skip files matching exclusion pattern
        if exclude_lower and exclude_lower in fname_lower:
            continue
        
        # Special case: "sperm cell" = binary segmentation mask
        # MUST contain both "sperm" AND "cell" together (e.g., "Sperm Cell_stack_6.tif")
        # Do NOT match just "Sperm 6.tif" (that's the raw image, not the mask)
        if organelle.lower() == "sperm cell":
            org_found = "sperm" in fname_lower and "cell" in fname_lower
        else:
            # For all other organelles, just check if organelle name is in filename
            # e.g., "pseudopod" matches "Pseudopod_stack_6.tif"
            org_found = org_lower in fname_lower
        
        # Check if sperm_id is in filename
        id_found = sperm_id_str in fname_lower
        
        if org_found and id_found:
            candidates.append(tiff_file)
    
    # Filter by registration status
    if registered:
        # Keep only files with _registration in name
        matches = [f for f in candidates if "_registration" in f.lower()]
    else:
        # Exclude files with _registration in name
        matches = [f for f in candidates if "_registration" not in f.lower()]
    
    if matches:
        return os.path.join(folder, matches[0])  # Return first match with full path
    
    reg_status = "registered" if registered else "unregistered"
    exclude_msg = f" (excluding '{exclude_pattern}')" if exclude_pattern else ""
    raise FileNotFoundError(
        f"No {reg_status} {organelle} file for sperm {sperm_id} in: {folder}{exclude_msg}\n"
        f"   💡 Expected: organelle name + sperm ID in filename (case-insensitive)\n"
        f"   💡 Available TIFFs: {sorted([f for f in os.listdir(folder) if f.lower().endswith('.tif')])}"
    )

def find_csv_by_pattern(folder: str, organelle: str, sperm_id: int) -> str:
    """Find tracking CSV file with flexible naming.
    
    Prefers "tracking results" files (primary tracking output).
    Falls back to any file with organelle name + sperm_id.
    
    Args:
        folder: Folder containing CSV files (includes subfolders)
        organelle: Organelle name ('MO', 'mitochondria', etc.)
        sperm_id: Sperm cell ID number
    
    Returns:
        Full path to matching CSV, or None if not found.
    """
    # Find all CSV files in folder and subfolders
    all_csvs = []
    for root, dirs, files in os.walk(folder):
        for f in files:
            if f.lower().endswith('.csv'):
                all_csvs.append(os.path.join(root, f))
    
    # Normalize search terms for case-insensitive matching
    org_lower = organelle.lower()
    sperm_id_str = str(sperm_id)
    
    # First try to find "tracking results" files (primary output)
    primary_matches = []
    fallback_matches = []
    
    for csv_file in all_csvs:
        fname_lower = os.path.basename(csv_file).lower()
        
        # Check if organelle name and sperm_id are in filename
        if org_lower in fname_lower and sperm_id_str in fname_lower:
            # Prefer "tracking results" files
            if "tracking results" in fname_lower:
                primary_matches.append(csv_file)
            else:
                fallback_matches.append(csv_file)
    
    # Return primary match if available, otherwise fallback
    if primary_matches:
        return primary_matches[0]
    elif fallback_matches:
        return fallback_matches[0]
    else:
        return None

def get_file_paths(sperm_id: int, base_dir: str, registered: bool = False):
    """Generate file paths for a sperm cell using flexible naming resolution.
    
    Uses glob patterns to find files with flexible naming conventions.
    Single organelles (pseudopod, nucleus, sperm_cell) are always unregistered.
    Multiple organelles (MO, mitochondria) can be registered or unregistered.
    
    Args:
        sperm_id: Sperm cell ID number
        base_dir: Parent directory containing 'Sperm N' folders
        registered: If True, finds registered versions of MO/mitochondria.
                   If False, finds unregistered versions.
    
    Returns:
        Dictionary with keys for each organelle and corresponding file paths.
    
    Raises:
        FileNotFoundError: If required files not found.
    """
    folder = os.path.join(base_dir, f"Sperm {sperm_id}")
    
    # Single organelles - always unregistered (no registration versions exist)
    paths = {
        "pseudopod": find_file_by_pattern(folder, "pseudopod", sperm_id, registered=False),
        "nucleus": find_file_by_pattern(folder, "nucleus", sperm_id, registered=False),
        "sperm_cell": find_file_by_pattern(folder, "sperm cell", sperm_id, registered=False),
        
        # Multiple organelles - can be registered or unregistered
        # IMPORTANT: MO search EXCLUDES unfused MO to prevent mismatching
        "MO": find_file_by_pattern(folder, "MO", sperm_id, registered=registered, exclude_pattern="unfused"),
        "mitochondria": find_file_by_pattern(folder, "mitochondria", sperm_id, registered=registered),
    }
    
    # Tracking CSVs (optional - return None if not found)
    mo_csv = find_csv_by_pattern(folder, "MO", sperm_id)
    mito_csv = find_csv_by_pattern(folder, "mitochondria", sperm_id)
    
    if mo_csv:
        paths["mo_csv"] = mo_csv
    if mito_csv:
        paths["mito_csv"] = mito_csv
    
    return paths

def get_unfused_mo_path(sperm_id: int, base_dir: str, registered: bool = False) -> str:
    """Get path to unfused MO stack for a sperm cell.
    
    Specifically targets files with "unfused" in the name to distinguish from
    regular (fused) MO stacks. Must contain "unfused" and "MO" in filename.
    
    Args:
        sperm_id: Sperm cell ID number
        base_dir: Parent directory containing 'Sperm N' folders
        registered: If True, finds registered version. If False, unregistered.
    
    Returns:
        Full path to unfused MO TIFF file.
    
    Raises:
        FileNotFoundError: If no unfused MO file found.
    """
    folder = os.path.join(base_dir, f"Sperm {sperm_id}")
    
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"Folder not found: {folder}")
    
    all_tiffs = [f for f in os.listdir(folder) if f.lower().endswith('.tif')]
    sperm_id_str = str(sperm_id)
    
    # Must contain BOTH "unfused" AND "mo" (case-insensitive)
    candidates = []
    for tiff_file in all_tiffs:
        fname_lower = tiff_file.lower()
        if "unfused" in fname_lower and "mo" in fname_lower and sperm_id_str in fname_lower:
            candidates.append(tiff_file)
    
    # Filter by registration status
    if registered:
        matches = [f for f in candidates if "_registration" in f.lower()]
    else:
        matches = [f for f in candidates if "_registration" not in f.lower()]
    
    if matches:
        return os.path.join(folder, matches[0])
    
    reg_status = "registered" if registered else "unregistered"
    raise FileNotFoundError(
        f"No {reg_status} unfused MO file for sperm {sperm_id} in: {folder}\n"
        f"   💡 Expected filename to contain: 'unfused', 'MO', and '{sperm_id}' (case-insensitive)\n"
        f"   💡 Available TIFFs: {sorted([f for f in os.listdir(folder) if f.lower().endswith('.tif')])}"
    )
def get_centroid(tif_path: str) -> np.ndarray:
    """Return centroid of the largest component in a binary 3D mask TIFF.
    
    Args:
        tif_path: Path to binary mask TIFF file.
    
    Returns:
        Centroid coordinates as (z, y, x) numpy array.
        Returns array of NaNs if no objects found.
    """
    mask = io.imread(tif_path)
    mask = (mask > 0).astype(np.uint8)
    props = measure.regionprops(measure.label(mask))
    return np.array(props[0].centroid) if props else np.array([np.nan, np.nan, np.nan])
