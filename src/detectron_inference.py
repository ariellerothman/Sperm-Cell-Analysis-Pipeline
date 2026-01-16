import os
import cv2
import numpy as np
import tifffile
import torch
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2 import model_zoo

def setup_predictor(model_weights_path, num_classes=6, threshold=0.05, use_gpu=False):
    """
    Set up Detectron2 predictor for inference.
    """
    cfg = get_cfg()
    cfg.merge_from_file(model_zoo.get_config_file("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml"))
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = threshold
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = num_classes
    cfg.MODEL.ROI_HEADS.NAME = "StandardROIHeads"
    cfg.MODEL.WEIGHTS = model_weights_path
    cfg.MODEL.DEVICE = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
    return DefaultPredictor(cfg)

def run_stack_inference(predictor, image_stack_path, output_base_dir, class_names):
    """
    Run inference on a 3D TIFF stack and save per-class binary masks.
    """
    os.makedirs(output_base_dir, exist_ok=True)
    overall_folder = os.path.join(output_base_dir, "overall_predictions")
    os.makedirs(overall_folder, exist_ok=True)

    for class_name in class_names:
        os.makedirs(os.path.join(output_base_dir, class_name), exist_ok=True)

    image_stack = tifffile.imread(image_stack_path)
    combined_masks_dict = {name: [] for name in class_names}

    for i, slice_img in enumerate(image_stack):
        if len(slice_img.shape) == 2:
            slice_img_color = cv2.cvtColor(slice_img, cv2.COLOR_GRAY2BGR)
        else:
            slice_img_color = slice_img

        outputs = predictor(slice_img_color)
        pred_classes = outputs["instances"].pred_classes.cpu().numpy()
        pred_masks = outputs["instances"].pred_masks.cpu().numpy()
        H, W = slice_img_color.shape[:2]

        for class_idx, class_name in enumerate(class_names):
            combined_mask = np.zeros((H, W), dtype=np.uint8)
            for j, pred_class in enumerate(pred_classes):
                if pred_class == class_idx:
                    combined_mask = cv2.bitwise_or(combined_mask, (pred_masks[j].astype(np.uint8)) * 255)
            combined_masks_dict[class_name].append(combined_mask)

        out_img = slice_img_color.copy()
        for j, pred_mask in enumerate(pred_masks):
            out_img[pred_mask] = (0, 0, 255)  # red overlay
        cv2.imwrite(os.path.join(overall_folder, f"slice_{i:03d}.png"), out_img)

    for class_name, mask_stack in combined_masks_dict.items():
        stack_path = os.path.join(output_base_dir, class_name, f"{class_name}_stack.tif")
        tifffile.imwrite(stack_path, np.array(mask_stack))
        print(f"✅ Saved {class_name} stack: {stack_path}")
