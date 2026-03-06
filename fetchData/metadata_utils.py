"""
Utilities for enhancing pipeline metadata (pipeline_metadata.json).

After the terrain mesh pipeline and ABL BC generator have run, this module
provides a function to post-process the metadata file so that:

- Absolute local paths are replaced with filenames only (portability).
- The output_files section (which lists local system paths) is removed.
- Tool version information is added (Python, OpenFOAM, library versions).
- ABL boundary-condition configuration is added from the ABL_BC_generator
  config object (atmospheric and turbulence parameters; not fvSchemes /
  fvSolution verbatim text).
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def _python_version() -> str:
    """Return the current Python version string."""
    return sys.version.split()[0]


def _library_version(package_name: str) -> Optional[str]:
    """Return the installed version of *package_name*, or None if unavailable."""
    try:
        from importlib.metadata import version
        return version(package_name)
    except Exception:
        return None


def _read_openfoam_version_from_config(terrain_config_path: Optional[str]) -> Optional[str]:
    """Try to read the OpenFOAM version from a terrain_config.yaml file."""
    if not terrain_config_path:
        return None
    config_path = Path(terrain_config_path)
    if not config_path.exists():
        return None
    try:
        import yaml
        with open(config_path) as fh:
            cfg = yaml.safe_load(fh) or {}
        return cfg.get("tool_versions", {}).get("openfoam_version")
    except Exception:
        return None


def _abl_config_to_dict(abl_config) -> dict:
    """
    Serialise the ABL configuration to a plain dictionary suitable for JSON.

    Only the atmospheric physics and turbulence parameters are included.
    Boundary condition templates (fvSchemes / fvSolution style entries) are
    intentionally excluded to avoid duplicating OpenFOAM file content in the
    metadata.
    """
    if abl_config is None:
        return {}

    result = {}

    atm = getattr(abl_config, "atmospheric", None)
    if atm is not None:
        result["atmospheric"] = {
            "u_star": getattr(atm, "u_star", None),
            "z0": getattr(atm, "z0", None),
            "h_bl": getattr(atm, "h_bl", None),
            "wind_dir_met": getattr(atm, "wind_dir_met", None),
            "U_ref": getattr(atm, "U_ref", None),
            "z_ref": getattr(atm, "z_ref", None),
        }

    turb = getattr(abl_config, "turbulence", None)
    if turb is not None:
        result["turbulence"] = {
            "Cmu": getattr(turb, "Cmu", None),
            "kappa": getattr(turb, "kappa", None),
        }

    # Include the declared OpenFOAM version from the openfoam config, but not
    # the full boundary-condition templates (wall functions, BC dicts, etc.).
    foam_cfg = getattr(abl_config, "openfoam", None)
    if foam_cfg is not None:
        result["openfoam_foam_version"] = getattr(foam_cfg, "foam_version", None)

    return result


def enhance_pipeline_metadata(
    case_dir: str,
    abl_config=None,
    dem_file: Optional[str] = None,
    roughness_file: Optional[str] = None,
    openfoam_version: Optional[str] = None,
    terrain_config_path: Optional[str] = None,
) -> None:
    """Post-process ``pipeline_metadata.json`` to improve FAIR-data compliance.

    This function is designed to be called immediately after both the terrain
    mesh pipeline and the ABL BC generator have finished for a given case
    directory.  It reads the existing ``pipeline_metadata.json``, applies the
    following transformations, and saves the result back to the same file.

    Transformations applied
    -----------------------
    1. **Path stripping** – absolute paths in ``input_files`` are replaced with
       the bare filename so the metadata is meaningful outside the local
       machine.
    2. **Output-file section removal** – ``output_files`` lists paths that only
       make sense locally, so the entire section is removed.
    3. **Tool-version recording** – ``pipeline_info`` is extended with:
       - ``python_version`` (auto-detected).
       - ``openfoam_version`` – taken from *openfoam_version* if supplied,
         otherwise from ``tool_versions.openfoam_version`` in
         *terrain_config_path*, then from the ABL config's declared foam
         version, or ``"unknown"`` as a final fallback.
       - ``terrain_mesh_generator_version`` – from the installed package if
         available.
       - ``abl_bc_generator_version`` – from the installed package if
         available.
    4. **ABL configuration** – a new ``abl_configuration`` section records the
       atmospheric and turbulence parameters used to generate the inlet
       boundary conditions.  fvSchemes / fvSolution file content is **not**
       included here to avoid redundancy with the generated OpenFOAM files.
    5. **Metadata-enhanced timestamp** – ``pipeline_info.metadata_enhanced_at``
       records when this function ran.

    Parameters
    ----------
    case_dir:
        Path to the rotation case directory that contains
        ``pipeline_metadata.json``.
    abl_config:
        An ``ABLConfig`` instance (from ``ABL_BC_generator.config``).  When
        ``None``, the ``abl_configuration`` section is omitted.
    dem_file:
        Full path to the DEM file used for this case (optional – used to
        derive the filename if the metadata already stores it).
    roughness_file:
        Full path to the roughness map file (optional).
    openfoam_version:
        OpenFOAM version string (e.g. ``"v2412"``).  If not supplied the
        version is read from the terrain config YAML, then from the ABL
        config, and finally falls back to ``"unknown"``.
    terrain_config_path:
        Path to ``terrain_config.yaml`` (or a variant copy).  Used to read
        the ``tool_versions.openfoam_version`` entry when *openfoam_version*
        is not explicitly provided.
    """
    meta_path = Path(case_dir) / "pipeline_metadata.json"
    if not meta_path.exists():
        return

    with open(meta_path, "r") as fh:
        metadata = json.load(fh)

    # ── 1. Strip absolute paths from input_files ──────────────────────────────
    input_files = metadata.get("input_files", {})
    raw_dem = input_files.get("dem_path") or (str(dem_file) if dem_file else None)
    raw_rmap = input_files.get("roughness_path") or (str(roughness_file) if roughness_file else None)
    metadata["input_files"] = {
        "dem_filename": Path(raw_dem).name if raw_dem else None,
        "roughness_filename": Path(raw_rmap).name if raw_rmap else None,
    }

    # ── 2. Remove the output_files section (local paths only) ─────────────────
    metadata.pop("output_files", None)

    # ── 3. Add tool versions ──────────────────────────────────────────────────
    pipeline_info = metadata.setdefault("pipeline_info", {})
    pipeline_info["python_version"] = _python_version()

    # Resolve OpenFOAM version: explicit arg > terrain config YAML > ABL config > "unknown"
    if openfoam_version:
        of_version = openfoam_version
    else:
        of_version = _read_openfoam_version_from_config(terrain_config_path)
        if not of_version and abl_config is not None:
            foam_cfg = getattr(abl_config, "openfoam", None)
            of_version = getattr(foam_cfg, "foam_version", None) if foam_cfg else None
        of_version = of_version or "unknown"
    pipeline_info["openfoam_version"] = of_version

    terrain_mesh_ver = _library_version("terrain-following-mesh-generator")
    pipeline_info["terrain_mesh_generator_version"] = terrain_mesh_ver or "unknown"

    abl_ver = _library_version("abl-bc-generator")
    pipeline_info["abl_bc_generator_version"] = abl_ver or "unknown"

    pipeline_info["metadata_enhanced_at"] = datetime.now().isoformat()

    # ── 4. Add ABL configuration ──────────────────────────────────────────────
    if abl_config is not None:
        metadata["abl_configuration"] = _abl_config_to_dict(abl_config)

    # ── Write back ────────────────────────────────────────────────────────────
    with open(meta_path, "w") as fh:
        json.dump(metadata, fh, indent=2, default=str)
