"""3D reconstruction and visualization of sperm cell organelles.

Extracts 3D mesh surfaces from segmented organelles using marching cubes and
renders animated orbit videos using PyVista.
"""

import os
import numpy as np
import imageio
from scipy.ndimage import gaussian_filter
from skimage import io as skio, filters, morphology, measure
from skimage.util import img_as_bool
from skimage.measure import marching_cubes
import pyvista as pv
from .config import (
    MESH_MIN_SIZE, MESH_THRESHOLD, MESH_BLUR, MESH_CLOSE_RADIUS,
    VIDEO_ZOOM_FACTOR, VIDEO_NUM_FRAMES, VIDEO_FPS
)

def extract_mesh_inside_sperm(
    path: str, sperm_path: str, voxel_size: tuple, min_sz: int = MESH_MIN_SIZE,
    thr_m: str = MESH_THRESHOLD, blur_s: float = MESH_BLUR, close_r: int = MESH_CLOSE_RADIUS
) -> tuple:
    """Extract 3D mesh from organelle stack, restricted to within sperm cell.
    
    Args:
        path: Path to organelle binary mask TIFF.
        sperm_path: Path to sperm cell boundary mask TIFF.
        voxel_size: Tuple of (z_um, y_um, x_um) voxel dimensions.
        min_sz: Minimum voxels for objects to include.
        thr_m: Thresholding method ('otsu' or numeric threshold).
        blur_s: Gaussian blur sigma (0 = no blur).
        close_r: Morphological closing radius (0 = no closing).
    
    Returns:
        Tuple of (vertices, faces) from marching cubes or (None, None) if no objects.
    """
    organelle = skio.imread(path).astype(np.float32)
    sperm_mask = skio.imread(sperm_path).astype(np.uint8)
    sperm_mask = img_as_bool(sperm_mask)

    if blur_s > 0:
        organelle = gaussian_filter(organelle, sigma=blur_s)

    thr = filters.threshold_otsu(organelle) if thr_m == 'otsu' else float(thr_m)
    binar = organelle > thr
    binar = morphology.remove_small_objects(binar, min_size=min_sz)
    if close_r > 0:
        binar = morphology.binary_closing(binar, footprint=morphology.ball(close_r))

    binar &= sperm_mask  # Restrict to within sperm mask

    lbl = measure.label(binar, connectivity=1)
    props = measure.regionprops(lbl)
    if not props:
        print(f"Warning: No objects found in {os.path.basename(path)}")
        return None, None
    keep_labels = [p.label for p in props if p.area >= min_sz]
    mask = np.isin(lbl, keep_labels)

    spacing = voxel_size
    verts, faces, *_ = marching_cubes(mask.astype(np.uint8), level=0.5, spacing=spacing)
    return verts, faces

def extract_mesh(
    path: str, voxel_size: tuple, min_sz: int = MESH_MIN_SIZE,
    thr_m: str = MESH_THRESHOLD, blur_s: float = MESH_BLUR, close_r: int = MESH_CLOSE_RADIUS
) -> tuple:
    """Extract 3D mesh from organelle binary stack using marching cubes.
    
    Applies thresholding, morphological cleaning, and connected component analysis
    before mesh generation. Uses configured defaults for mesh quality tuning.
    
    Args:
        path: Path to organelle binary mask TIFF file.
        voxel_size: Tuple of (z_um, y_um, x_um) voxel dimensions in micrometers.
        min_sz: Minimum voxels for objects to include (removes noise).
        thr_m: Thresholding method - 'otsu' (auto) or numeric value (e.g., '128').
        blur_s: Gaussian blur sigma for smoothing (0 = no blur).
        close_r: Morphological closing radius for filling holes (0 = no closing).
    
    Returns:
        Tuple of (vertices, faces) from marching cubes or (None, None) if no objects.
        vertices: Array of shape (N_verts, 3) with XYZ coordinates in micrometers.
        faces: Array of shape (N_faces, 3) with vertex indices for triangles.
    """
    stack = skio.imread(path).astype(np.float32)
    if blur_s > 0:
        stack = gaussian_filter(stack, sigma=blur_s)
    thr = filters.threshold_otsu(stack) if thr_m == 'otsu' else float(thr_m)
    binar = stack > thr
    binar = morphology.remove_small_objects(binar, min_size=min_sz)
    if close_r > 0:
        binar = morphology.binary_closing(binar, footprint=morphology.ball(close_r))
    lbl = measure.label(binar, connectivity=1)
    props = measure.regionprops(lbl)
    if not props:
        print(f"No objects found in {os.path.basename(path)}")
        return None, None
    keep_labels = [p.label for p in props if p.area >= min_sz]
    mask = np.isin(lbl, keep_labels)
    spacing = voxel_size
    verts, faces, *_ = marching_cubes(mask.astype(np.uint8), level=0.5, spacing=spacing)
    return verts, faces

def build_3d_scene(
    objects: list, voxel_size: tuple, min_sz: int = MESH_MIN_SIZE,
    thr_m: str = MESH_THRESHOLD, close_r: int = MESH_CLOSE_RADIUS,
    sperm_mask_path: str = None
) -> pv.Plotter:
    """Build 3D PyVista scene with organelle meshes.
    
    Creates an off-screen plotter with all organelles rendered as colored meshes.
    Selected organelles (mitochondria, nucleus) are restricted to within the sperm
    cell boundary if mask provided.
    
    Args:
        objects: List of organelle dicts with keys 'name', 'path', 'color', 'opacity', 'blur'.
        voxel_size: Tuple of (z_um, y_um, x_um) voxel dimensions.
        min_sz: Minimum voxels for mesh objects.
        thr_m: Thresholding method ('otsu' or numeric).
        close_r: Morphological closing radius.
        sperm_mask_path: Optional path to sperm boundary mask TIFF.
    
    Returns:
        PyVista Plotter object with all meshes added and ready for rendering.
    """
    plotter = pv.Plotter(off_screen=True)
    plotter.set_background('white')
    print("Extracting meshes:")
    mesh_count = 0
    for o in objects:
        try:
            # Try masking for selected organelles, but skip if dimensions don't match
            if o["name"] in ["mitochondria", "nucleus"] and sperm_mask_path is not None:
                v, f = extract_mesh_inside_sperm(
                    o["path"], sperm_mask_path, voxel_size, min_sz, thr_m, o.get("blur", 0.0), close_r
                )
            else:
                # For MO and other organelles, extract without sperm mask
                # (MO stack may have different dimensions than registered sperm mask)
                v, f = extract_mesh(
                    o["path"], voxel_size, min_sz, thr_m, o.get("blur", 0.0), close_r
                )
            if v is not None and f is not None:
                print(f"  {o['name']}: {v.shape[0]} verts, {f.shape[0]} faces")
                faces_pv = np.hstack([np.full((f.shape[0], 1), 3), f]).astype(np.int64)
                mesh = pv.PolyData(v, faces_pv)
                plotter.add_mesh(
                    mesh,
                    color=o["color"],
                    opacity=o["opacity"],
                    smooth_shading=True,
                    name=o['name']
                )
                mesh_count += 1
            else:
                print(f"  ✗ {o['name']}: No mesh extracted")
        except Exception as e:
            print(f"  ✗ {o['name']}: Error during extraction - {str(e)[:60]}")
    
    if mesh_count == 0:
        print("\nWARNING: No meshes were successfully extracted!")
        print("   Check that organelle files exist and contain valid data.")
    else:
        print(f"\nSuccessfully extracted {mesh_count} organelle meshes")
    
    return plotter

# ------------------ Orbit Animation ------------------
def render_orbit_video(
    plotter: pv.Plotter, output_path: str, zoom_out_factor: float = VIDEO_ZOOM_FACTOR,
    num_frames: int = VIDEO_NUM_FRAMES, fps: int = VIDEO_FPS
) -> None:
    """Generate orbital rotation video by capturing frames with incremental camera rotation.
    
    Args:
        plotter: PyVista Plotter object with meshes already added.
        output_path: Path to save output GIF file.
        zoom_out_factor: Camera zoom multiplier.
        num_frames: Number of frames in rotation.
        fps: Frames per second.
    """
    if len(plotter.actors) == 0:
        raise ValueError("Plotter has no meshes to render")
    
    print(f"🎥 Rendering {num_frames}-frame orbit video...")
    
    try:
        # Reset camera and set isometric view
        plotter.reset_camera()
        plotter.view_isometric()
        plotter.camera.zoom(zoom_out_factor)
        
        frames = []
        
        for i in range(num_frames):
            try:
                # Calculate rotation angle for full 360° rotation
                angle = (i / num_frames) * 360.0
                
                # Apply isometric view with rotation around Z axis
                plotter.view_isometric()
                plotter.camera.azimuth = angle
                plotter.render()
                img = plotter.screenshot(return_img=True)
                frames.append(img)
                
                if (i + 1) % 15 == 0:
                    print(f"  Frame {i + 1}/{num_frames}")
                    
            except Exception as e:
                print(f"Error on frame {i + 1}: {str(e)[:60]}")
                continue
        
        if len(frames) == 0:
            raise ValueError("No frames were captured")
        
        # Save video
        print(f"💾 Saving {len(frames)} frames to video...")
        imageio.mimsave(output_path, frames, fps=fps)
        print(f"Video saved successfully! ({len(frames)} frames)")
        
    except Exception as e:
        raise ValueError(f"Video rendering failed: {str(e)}")