"""
NAE™ Midpoint Accuracy Metric (MAM) geometric audit utilities.

The MAM audit is intentionally limited to objective workspace geometry: grid
calibration, peg coordinate extraction inputs, and signed/absolute deviation
from the horizontal midpoint axis. It does not infer, diagnose, or score neural
or clinical status from the participant data.
"""

from __future__ import annotations

import csv
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


GRID_CELLS_X = 10
GRID_CELLS_Y = 10
DEFAULT_OUTPUT_CSV = "MAM_Audit_Results.csv"


@dataclass(frozen=True)
class PegPlacement:
    """A single detected or manually reviewed peg coordinate in image pixels."""

    peg_id: int
    x: float
    y: float


@dataclass(frozen=True)
class MamAuditConfig:
    """Configuration for the standardized 10x10 MAM grid audit."""

    grid_cells_x: int = GRID_CELLS_X
    grid_cells_y: int = GRID_CELLS_Y
    output_csv: str = DEFAULT_OUTPUT_CSV

    def validate(self) -> None:
        if self.grid_cells_x <= 0 or self.grid_cells_y <= 0:
            raise ValueError("Grid dimensions must be positive integers.")


def read_image_dimensions(image_path: str | Path) -> tuple[int, int]:
    """
    Return image width and height for PNG, JPEG, or GIF files without mutating it.

    This keeps the audit non-invasive and avoids making OpenCV/NumPy/Pandas
    mandatory runtime dependencies for CSV-only geometric analysis.
    """

    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    with path.open("rb") as image_file:
        header = image_file.read(24)
        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            width, height = struct.unpack(">II", header[16:24])
            return width, height

        if header.startswith((b"GIF87a", b"GIF89a")):
            width, height = struct.unpack("<HH", header[6:10])
            return width, height

        if header.startswith(b"\xff\xd8"):
            image_file.seek(2)
            while True:
                marker_prefix = image_file.read(1)
                if marker_prefix == b"":
                    break
                if marker_prefix != b"\xff":
                    continue

                marker = image_file.read(1)
                while marker == b"\xff":
                    marker = image_file.read(1)

                start_of_frame_markers = {
                    b"\xc0", b"\xc1", b"\xc2", b"\xc3", b"\xc5",
                    b"\xc6", b"\xc7", b"\xc9", b"\xca", b"\xcb",
                    b"\xcd", b"\xce", b"\xcf",
                }
                if marker in start_of_frame_markers:
                    image_file.read(3)
                    height, width = struct.unpack(">HH", image_file.read(4))
                    return width, height

                segment_length_bytes = image_file.read(2)
                if len(segment_length_bytes) != 2:
                    break
                segment_length = struct.unpack(">H", segment_length_bytes)[0]
                image_file.seek(segment_length - 2, 1)

    raise ValueError(f"Unsupported or unreadable image format: {path}")


def default_review_pegs() -> list[PegPlacement]:
    """
    Return deterministic demonstration coordinates for SOP dry-runs only.

    Production use should pass reviewed contour-detection results or manually
    verified coordinates through the ``detected_pegs`` argument.
    """

    return [
        PegPlacement(peg_id=1, x=300, y=480),
        PegPlacement(peg_id=2, x=400, y=482),
        PegPlacement(peg_id=3, x=500, y=478),
        PegPlacement(peg_id=4, x=600, y=481),
        PegPlacement(peg_id=5, x=700, y=480),
    ]


def normalize_pegs(
    detected_pegs: Iterable[PegPlacement | dict[str, float]],
) -> list[PegPlacement]:
    """Normalize dataclass or dictionary peg inputs into validated placements."""

    normalized: list[PegPlacement] = []
    for index, peg in enumerate(detected_pegs, start=1):
        if isinstance(peg, PegPlacement):
            placement = peg
        else:
            placement = PegPlacement(
                peg_id=int(peg.get("id", peg.get("peg_id", index))),
                x=float(peg["x"]),
                y=float(peg["y"]),
            )

        if placement.x < 0 or placement.y < 0:
            raise ValueError(f"Peg {placement.peg_id} has negative coordinates.")
        normalized.append(placement)

    if not normalized:
        raise ValueError("At least one peg placement is required for a MAM audit.")

    return normalized


def mam_geometric_audit(
    image_path: str | Path | None = None,
    *,
    image_dimensions: tuple[int, int] | None = None,
    detected_pegs: Iterable[PegPlacement | dict[str, float]] | None = None,
    config: MamAuditConfig | None = None,
) -> list[dict[str, float | int | str]]:
    """
    Run the SOP-aligned MAM geometric audit and write a portable CSV file.

    Parameters:
        image_path: Optional path to the post-session workspace capture.
        image_dimensions: Optional ``(width, height)`` tuple, useful for tested
            pipelines that already know the capture dimensions.
        detected_pegs: Reviewed peg coordinates from contour detection or manual
            validation. If omitted, demonstration coordinates are used and every
            row is marked as ``Simulated Review Coordinate``.
        config: Grid and output path settings.

    Returns:
        The same row dictionaries written to the CSV export.
    """

    audit_config = config or MamAuditConfig()
    audit_config.validate()

    if image_dimensions is None:
        if image_path is None:
            raise ValueError("Provide image_path or image_dimensions for MAM audit.")
        width, height = read_image_dimensions(image_path)
    else:
        width, height = image_dimensions

    if width <= 0 or height <= 0:
        raise ValueError("Image dimensions must be positive.")

    pegs = normalize_pegs(detected_pegs or default_review_pegs())
    true_center_y = height / 2.0
    grid_cell_width = width / audit_config.grid_cells_x
    grid_cell_height = height / audit_config.grid_cells_y
    coordinate_source = (
        "Reviewed Coordinate"
        if detected_pegs is not None
        else "Simulated Review Coordinate"
    )

    results: list[dict[str, float | int | str]] = []
    for peg in pegs:
        if peg.x > width or peg.y > height:
            raise ValueError(f"Peg {peg.peg_id} falls outside the image bounds.")

        delta = peg.y - true_center_y
        results.append(
            {
                "Peg_ID": peg.peg_id,
                "X_Coord": peg.x,
                "Y_Coord": peg.y,
                "Grid_Column": min(
                    audit_config.grid_cells_x,
                    int(peg.x // grid_cell_width) + 1,
                ),
                "Grid_Row": min(
                    audit_config.grid_cells_y,
                    int(peg.y // grid_cell_height) + 1,
                ),
                "Center_Axis_Y": true_center_y,
                "Center_Axis_Delta": delta,
                "Absolute_Delta": abs(delta),
                "Normalized_Delta_Cells": delta / grid_cell_height,
                "Metric": "Midpoint Accuracy Metric",
                "Coordinate_Source": coordinate_source,
            }
        )

    fieldnames: Sequence[str] = tuple(results[0].keys())
    with Path(audit_config.output_csv).open(
        "w", newline="", encoding="utf-8"
    ) as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    return results


if __name__ == "__main__":
    mam_geometric_audit("participant_workspace_final.jpg")
