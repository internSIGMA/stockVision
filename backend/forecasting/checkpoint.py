"""
Model Checkpointing and Resumable Training Module for StockVision Forecasting.

Features:
1. Persists trained LightGBM models to disk (checkpoints folder) with metadata.
2. Supports fast resumption if training or crawling was interrupted.
3. Freshness detection: automatically triggers retraining when new trading data is ingested.
"""

import os
import json
from pathlib import Path
from datetime import datetime
import joblib

from .config import MODELS_DIR
from .logger import logger

CHECKPOINT_DIR = MODELS_DIR / "checkpoints"
MANIFEST_FILE = CHECKPOINT_DIR / "manifest.json"


def ensure_checkpoint_dir():
    """Ensure the checkpoints directory exists."""
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    return CHECKPOINT_DIR


def load_manifest():
    """Load the checkpoint manifest tracking all saved models."""
    ensure_checkpoint_dir()
    if not MANIFEST_FILE.exists():
        return {}
    try:
        with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("[Checkpoint] Error reading manifest.json: %s. Rebuilding.", e)
        return {}


def save_manifest(manifest):
    """Save the checkpoint manifest to disk."""
    ensure_checkpoint_dir()
    try:
        with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, default=str)
    except Exception as e:
        logger.error("[Checkpoint] Error saving manifest.json: %s", e)


def _get_key(identifier, target, model_type="cluster"):
    """Unique key for the model in manifest."""
    return f"{model_type}_{identifier}_{target.lower()}"


def _get_filename(identifier, target, model_type="cluster"):
    """Filename for the model binary."""
    return f"{model_type}_{identifier}_{target.lower()}.joblib"


def save_model_checkpoint(identifier, target, model, metadata=None, model_type="cluster"):
    """
    Save a trained model and its metadata to the checkpoint directory.

    Args:
        identifier: int (cluster_id) or str (symbol)
        target: str ('open', 'high', 'low', 'close', 'volume')
        model: trained model object (e.g. LGBMRegressor)
        metadata: dict containing metrics, last_data_date, sample_count, etc.
        model_type: 'cluster' or 'symbol'
    """
    try:
        ensure_checkpoint_dir()
        filename = _get_filename(identifier, target, model_type)
        filepath = CHECKPOINT_DIR / filename
        key = _get_key(identifier, target, model_type)

        # 1. Save model binary
        joblib.dump(model, filepath, compress=3)

        # 2. Update manifest
        manifest = load_manifest()
        meta = metadata.copy() if metadata else {}
        meta.update({
            "model_type": model_type,
            "identifier": str(identifier),
            "target": target.lower(),
            "filename": filename,
            "saved_at": datetime.now().isoformat(),
        })
        manifest[key] = meta
        save_manifest(manifest)

        logger.info("[Checkpoint] Saved model checkpoint for %s %s / %s -> %s",
                    model_type, identifier, target.upper(), filename)
        return str(filepath)
    except Exception as e:
        logger.error("[Checkpoint] Failed to save checkpoint for %s %s / %s: %s",
                     model_type, identifier, target, e)
        return None


def load_model_checkpoint(identifier, target, model_type="cluster"):
    """
    Load a trained model and its metadata from disk.

    Returns:
        (model, metadata) or (None, None) if not found or corrupted.
    """
    try:
        ensure_checkpoint_dir()
        filename = _get_filename(identifier, target, model_type)
        filepath = CHECKPOINT_DIR / filename
        key = _get_key(identifier, target, model_type)

        if not filepath.exists():
            return None, None

        manifest = load_manifest()
        metadata = manifest.get(key, {})

        model = joblib.load(filepath)
        logger.info("[Checkpoint] Loaded existing model checkpoint: %s (Trained: %s)",
                    filename, metadata.get("last_trained_date", metadata.get("saved_at", "N/A")))
        return model, metadata
    except Exception as e:
        logger.warning("[Checkpoint] Could not load checkpoint for %s %s / %s: %s",
                       model_type, identifier, target, e)
        return None, None


def is_checkpoint_fresh(identifier, target, latest_data_date, model_type="cluster"):
    """
    Check if a saved model checkpoint is fresh (trained up to the latest data date).

    Args:
        identifier: cluster_id or symbol
        target: 'open', 'high', 'low', 'close', 'volume'
        latest_data_date: date string (e.g. '2026-08-27') or datetime/Timestamp
        model_type: 'cluster' or 'symbol'

    Returns:
        bool: True if checkpoint exists and last_trained_date >= latest_data_date
    """
    if latest_data_date is None:
        return False

    key = _get_key(identifier, target, model_type)
    filename = _get_filename(identifier, target, model_type)
    filepath = CHECKPOINT_DIR / filename

    if not filepath.exists():
        return False

    manifest = load_manifest()
    entry = manifest.get(key)
    if not entry:
        return False

    last_trained = entry.get("last_trained_date")
    if not last_trained:
        return False

    # Format comparison strings (YYYY-MM-DD)
    last_trained_str = str(last_trained)[:10]
    latest_data_str = str(latest_data_date)[:10]

    is_fresh = last_trained_str >= latest_data_str
    if not is_fresh:
        logger.info("[Checkpoint] Checkpoint for %s %s / %s is outdated (Model: %s < Data: %s). Retraining needed.",
                    model_type, identifier, target, last_trained_str, latest_data_str)
    return is_fresh


def get_all_checkpoints_summary():
    """Return list of all saved checkpoints and their metadata."""
    manifest = load_manifest()
    summary = []
    for key, val in manifest.items():
        summary.append(val)
    return summary


def clear_all_checkpoints():
    """Delete all model checkpoints from disk."""
    try:
        ensure_checkpoint_dir()
        for f in CHECKPOINT_DIR.glob("*.joblib"):
            try:
                f.unlink()
            except Exception:
                pass
        if MANIFEST_FILE.exists():
            MANIFEST_FILE.unlink()
        logger.info("[Checkpoint] All model checkpoints cleared.")
        return True
    except Exception as e:
        logger.error("[Checkpoint] Error clearing checkpoints: %s", e)
        return False
