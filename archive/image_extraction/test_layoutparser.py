#!/usr/bin/env python3
"""Test what layoutparser models are available."""

import layoutparser as lp
import sys

def test_layoutparser_models():
    """Test which layoutparser models are available."""
    
    print("Testing LayoutParser model availability...")
    print("=" * 50)
    
    models_to_test = [
        {
            "name": "Detectron2LayoutModel", 
            "config": "lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config",
            "label_map": {0:"Text",1:"Title",2:"List",3:"Table",4:"Figure"}
        },
        {
            "name": "PaddleDetectionLayoutModel",
            "config": "lp://PubLayNet/ppyolov2_r50vd_dcn_365e_publaynet/config", 
            "label_map": {0:"Text",1:"Title",2:"List",3:"Table",4:"Figure"}
        },
        {
            "name": "EfficientDetLayoutModel",
            "config": "lp://PubLayNet/tf_efficientdet_d1/config",
            "label_map": {0:"Text",1:"Title",2:"List",3:"Table",4:"Figure"}
        }
    ]
    
    available_models = []
    
    for model_info in models_to_test:
        model_name = model_info["name"]
        try:
            print(f"Testing {model_name}...")
            
            if hasattr(lp, model_name):
                model_class = getattr(lp, model_name)
                print(f"  ✓ {model_name} class found")
                
                # Try to instantiate (but don't download if we can avoid it)
                try:
                    if model_name == "Detectron2LayoutModel":
                        model = model_class(
                            config_path=model_info["config"],
                            label_map=model_info["label_map"],
                            extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.5],
                            device="cpu"
                        )
                    elif model_name == "PaddleDetectionLayoutModel":
                        model = model_class(
                            config_path=model_info["config"],
                            label_map=model_info["label_map"],
                            threshold=0.5,
                            device="cpu"
                        )
                    elif model_name == "EfficientDetLayoutModel":
                        model = model_class(
                            config_path=model_info["config"],
                            label_map=model_info["label_map"],
                            device="cpu"
                        )
                    
                    print(f"  ✓ {model_name} instantiated successfully!")
                    available_models.append(model_name)
                    
                except Exception as e:
                    print(f"  ✗ {model_name} instantiation failed: {e}")
                    
            else:
                print(f"  ✗ {model_name} class not found in layoutparser")
                
        except Exception as e:
            print(f"  ✗ Error testing {model_name}: {e}")
        
        print()
    
    print("Summary:")
    print("=" * 50)
    if available_models:
        print("Available models:")
        for model in available_models:
            print(f"  ✓ {model}")
    else:
        print("No models are available.")
        print("You may need to install additional dependencies:")
        print("  - For Detectron2: pip install detectron2 (may require specific torch version)")
        print("  - For PaddleDetection: pip install paddlepaddle paddledet")
        print("  - For EfficientDet: Should work with current installation")
    
    return available_models

if __name__ == "__main__":
    available = test_layoutparser_models()
    if not available:
        sys.exit(1)