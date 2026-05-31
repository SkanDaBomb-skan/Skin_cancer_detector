"""
Application Configuration
=========================
Centralized configuration for the Skin Cancer Detection Platform.
All settings are organized by category for easy management.
"""

import os

# ---------------------------------------------------------------------------
# Base directory — resolved once so every path is relative to it
# ---------------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Default / development configuration."""

    # ── Security ──────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get(
        "SECRET_KEY", "dermavision-dev-key-change-in-production"
    )
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "password123")

    # ── File uploads ──────────────────────────────────────────────────────
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

    # ── Database (SQLite — zero‑config) ───────────────────────────────────
    DATABASE_PATH = os.path.join(BASE_DIR, "database", "dermavision.db")

    # ── ML Model ──────────────────────────────────────────────────────────
    MODEL_PATH = os.path.join(BASE_DIR, "model", "vgg16_malignant_benign.h5")
    IMG_SIZE = (224, 224)

    # ── HAM10000 — 7 class labels with medical metadata ──────────────────
    CLASS_LABELS = {
        0: {
            "name": "Actinic Keratoses",
            "short": "AKIEC",
            "risk": "Pre-malignant",
            "description": (
                "Actinic keratoses are rough, scaly patches on the skin caused "
                "by years of sun exposure. They are considered pre-cancerous "
                "and may develop into squamous cell carcinoma if left untreated."
            ),
            "recommendation": (
                "Consult a dermatologist for evaluation. Treatment options "
                "include cryotherapy, topical medications, or photodynamic therapy."
            ),
        },
        1: {
            "name": "Basal Cell Carcinoma",
            "short": "BCC",
            "risk": "Malignant",
            "description": (
                "Basal cell carcinoma is the most common form of skin cancer. "
                "It arises from the basal cells in the deepest layer of the "
                "epidermis. While it rarely metastasizes, it can cause "
                "significant local tissue destruction."
            ),
            "recommendation": (
                "Seek prompt medical attention. Surgical excision is typically "
                "the first-line treatment. Mohs surgery may be recommended "
                "for lesions in cosmetically sensitive areas."
            ),
        },
        2: {
            "name": "Benign Keratosis",
            "short": "BKL",
            "risk": "Benign",
            "description": (
                "Benign keratoses include seborrheic keratoses, solar "
                "lentigines, and lichen planus–like keratoses. These are "
                "non-cancerous growths that typically don't require treatment."
            ),
            "recommendation": (
                "Generally no treatment is required. If the lesion is "
                "bothersome or cosmetically concerning, removal options "
                "are available. Monitor for any changes."
            ),
        },
        3: {
            "name": "Dermatofibroma",
            "short": "DF",
            "risk": "Benign",
            "description": (
                "Dermatofibromas are common, harmless skin growths that often "
                "appear as small, firm bumps. They are usually brownish and "
                "may feel hard when pressed (dimple sign)."
            ),
            "recommendation": (
                "No treatment is necessary unless symptomatic. If it causes "
                "discomfort or cosmetic concern, surgical excision is an option."
            ),
        },
        4: {
            "name": "Melanoma",
            "short": "MEL",
            "risk": "Malignant",
            "description": (
                "Melanoma is the most dangerous form of skin cancer, arising "
                "from melanocytes. It can spread rapidly to other organs if "
                "not caught early. Early detection is crucial for survival."
            ),
            "recommendation": (
                "URGENT: Seek immediate medical evaluation. Early-stage "
                "melanoma has a high survival rate with surgical excision. "
                "Advanced cases may require immunotherapy or targeted therapy."
            ),
        },
        5: {
            "name": "Melanocytic Nevi",
            "short": "NV",
            "risk": "Benign",
            "description": (
                "Melanocytic nevi (moles) are benign neoplasms of melanocytes. "
                "Most moles are harmless, but atypical moles should be "
                "monitored for changes using the ABCDE rule."
            ),
            "recommendation": (
                "Routine monitoring is recommended. Watch for asymmetry, "
                "border irregularity, color variation, diameter > 6 mm, "
                "and evolution (ABCDE criteria). Annual skin checks advised."
            ),
        },
        6: {
            "name": "Vascular Lesions",
            "short": "VASC",
            "risk": "Benign",
            "description": (
                "Vascular lesions include angiomas, angiokeratomas, and "
                "pyogenic granulomas. These are caused by abnormal blood "
                "vessel growth and are usually benign."
            ),
            "recommendation": (
                "Typically benign and may not require treatment. Laser therapy "
                "or surgical removal can be considered for cosmetic purposes "
                "or if bleeding occurs."
            ),
        },
    }

    # ── Risk‑level metadata (used by the UI) ──────────────────────────────
    RISK_COLORS = {
        "Benign": {"bg": "#dcfce7", "text": "#166534", "accent": "#22c55e"},
        "Pre-malignant": {"bg": "#fef9c3", "text": "#854d0e", "accent": "#eab308"},
        "Malignant": {"bg": "#fee2e2", "text": "#991b1b", "accent": "#ef4444"},
    }
