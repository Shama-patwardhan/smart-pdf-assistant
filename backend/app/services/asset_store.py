"""Service for managing document-centric assets like chat history and future generated content.

Stores data in JSON format under data/assets/{document_name}/{asset_type}.json
"""
import json
import logging
import shutil
from pathlib import Path
from backend.app.config import settings

logger = logging.getLogger(__name__)

ASSETS_DIR = settings.UPLOAD_FOLDER.parent / "assets"

def get_asset_path(filename: str, asset_type: str) -> Path:
    """Gets the path for a specific asset type of a document."""
    # Handle the global scope or empty scope as global
    scope = "global" if not filename or filename == "global" else filename
    return ASSETS_DIR / scope / f"{asset_type}.json"

def get_asset(filename: str, asset_type: str) -> list | dict | None:
    """Retrieves an asset, returning None if it doesn't exist."""
    asset_path = get_asset_path(filename, asset_type)
    if not asset_path.exists():
        return None
        
    try:
        with open(asset_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read asset {asset_type} for {filename}: {e}")
        return None

def save_asset(filename: str, asset_type: str, data: list | dict) -> None:
    """Saves data to an asset file in JSON format."""
    asset_path = get_asset_path(filename, asset_type)
    
    try:
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        with open(asset_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Successfully saved {asset_type} for {filename}.")
    except Exception as e:
        logger.error(f"Failed to save asset {asset_type} for {filename}: {e}")
        raise RuntimeError(f"Failed to save {asset_type}: {str(e)}")

def delete_assets(filename: str) -> None:
    """Deletes all assets for a given document."""
    if not filename or filename == "global":
        return
        
    doc_assets_dir = ASSETS_DIR / filename
    if doc_assets_dir.exists() and doc_assets_dir.is_dir():
        try:
            shutil.rmtree(doc_assets_dir)
            logger.info(f"Successfully deleted all assets for {filename}.")
        except Exception as e:
            logger.error(f"Failed to delete assets directory for {filename}: {e}")
            raise RuntimeError(f"Failed to delete assets for {filename}: {str(e)}")

def clear_asset(filename: str, asset_type: str) -> None:
    """Clears (deletes) a specific asset file for a document."""
    asset_path = get_asset_path(filename, asset_type)
    if asset_path.exists():
        try:
            asset_path.unlink()
            logger.info(f"Successfully cleared {asset_type} for {filename}.")
        except Exception as e:
            logger.error(f"Failed to clear {asset_type} for {filename}: {e}")
            raise RuntimeError(f"Failed to clear {asset_type}: {str(e)}")
