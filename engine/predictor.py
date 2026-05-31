"""
ML Prediction Engine
====================
Handles model loading, image preprocessing, and inference.
Separated from Flask routes for clean architecture and testability.
"""

import json
import os
import numpy as np
from datetime import datetime
from config import Config

# ---------------------------------------------------------------------------
# Lazy model loading — avoids import-time TensorFlow overhead
# ---------------------------------------------------------------------------
_model = None


def _load_model():
    """Load the Keras model from disk (once)."""
    global _model
    if _model is None:
        model_path = Config.MODEL_PATH
        if os.path.exists(model_path):
            from keras.models import Model
            from keras.layers import Dense, Flatten, Dropout
            from keras.applications import VGG16
            
            # Construct architecture manually using Functional API to perfectly match the saved H5 structure
            # (Sequential with nested models causes layer count mismatches in Keras 3 load_weights)
            base_model = VGG16(weights=None, include_top=False, input_shape=(224, 224, 3))
            
            x = Flatten(name='flatten')(base_model.output)
            x = Dense(256, activation='relu', name='dense')(x)
            x = Dropout(0.5, name='dropout')(x)
            outputs = Dense(1, activation='sigmoid', name='dense_1')(x)
            
            _model = Model(inputs=base_model.input, outputs=outputs)
            
            _model.load_weights(model_path)
            print(f"[DermaVision] Model weights loaded from {model_path}")
        else:
            print(
                f"[DermaVision] WARNING — model file not found at {model_path}. "
                "Predictions will use demo mode (random)."
            )
    return _model


def preprocess_image(image_path: str) -> np.ndarray:
    """
    Load an image from *image_path*, resize it to the expected input
    dimensions, and normalise pixel values to [0, 1].

    Returns:
        4-D numpy array of shape (1, H, W, 3)
    """
    from keras.utils import load_img, img_to_array

    img = load_img(image_path, target_size=Config.IMG_SIZE)
    arr = img_to_array(img) / 255.0
    return np.expand_dims(arr, axis=0)


def predict(image_path: str) -> dict:
    """
    Run inference on the image at *image_path*.

    Returns a dict with:
        - diagnosis        (str)  — full class name
        - short_code       (str)  — abbreviated code (e.g. MEL)
        - risk_level       (str)  — Benign / Pre-malignant / Malignant
        - confidence       (float) — percentage (0–100)
        - description      (str)  — medical description
        - recommendation   (str)  — next-step guidance
        - top_3            (list[dict]) — top 3 predictions with name & %
    """
    model = _load_model()
    img_array = preprocess_image(image_path)

    labels = Config.CLASS_LABELS

    if model is not None:
        # ── Real inference ────────────────────────────────────────────
        raw = model.predict(img_array, verbose=0)

        # Handle both binary (sigmoid) and multi-class (softmax) outputs
        num_classes = raw.shape[-1]
        probs = {i: 0.0 for i in labels}
        
        if num_classes == 1:
            # Binary model: output is P(malignant)
            p_mal = float(raw[0][0])
            if p_mal > 0.5:
                idx = 4  # Melanoma (Malignant)
                confidence = p_mal * 100
            else:
                idx = 5  # Melanocytic Nevi (Benign)
                confidence = (1 - p_mal) * 100
            probs[4] = p_mal
            probs[5] = 1.0 - p_mal
            
        elif num_classes == 2:
            # Binary model with softmax output (assume 0=Benign, 1=Malignant)
            p_benign = float(raw[0][0])
            p_mal = float(raw[0][1])
            
            probs[5] = p_benign  # Map to Melanocytic Nevi (Benign)
            probs[4] = p_mal     # Map to Melanoma (Malignant)
            
            if p_mal > p_benign:
                idx = 4
                confidence = p_mal * 100
            else:
                idx = 5
                confidence = p_benign * 100
                
        else:
            # Multi-class softmax (7 classes)
            for i in range(min(num_classes, len(labels))):
                probs[i] = float(raw[0][i])
            idx = int(np.argmax(raw[0]))
            confidence = probs[idx] * 100
    else:
        # ── Demo mode (no model file) ─────────────────────────────────
        probs = _demo_probabilities()
        idx = max(probs, key=probs.get)
        confidence = probs[idx] * 100

    info = labels[idx]

    # Top-3 predictions
    sorted_preds = sorted(probs.items(), key=lambda x: x[1], reverse=True)[:3]
    top_3 = [
        {"name": labels[i]["name"], "confidence": round(p * 100, 1)}
        for i, p in sorted_preds
    ]

    return {
        "diagnosis": info["name"],
        "short_code": info["short"],
        "risk_level": info["risk"],
        "confidence": round(confidence, 1),
        "description": info["description"],
        "recommendation": info["recommendation"],
        "top_3": top_3,
        "top_3_json": json.dumps(top_3),
    }


# ---------------------------------------------------------------------------
# Demo helpers
# ---------------------------------------------------------------------------

def _demo_probabilities() -> dict:
    """Generate plausible random probabilities for demo / testing."""
    raw = np.random.dirichlet(np.ones(7))
    return {i: float(raw[i]) for i in range(7)}


def save_upload(file, upload_folder: str) -> str:
    """
    Save an uploaded file with a timestamped name to avoid collisions.

    Returns the relative path (from project root) suitable for serving
    as a static asset.
    """
    os.makedirs(upload_folder, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = file.filename.replace(" ", "_")
    filename = f"{ts}_{safe}"
    full_path = os.path.join(upload_folder, filename)
    file.save(full_path)
    return full_path
