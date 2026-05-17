import csv
import struct
import tempfile
import unittest
from pathlib import Path

from mam_audit import (
    MamAuditConfig,
    PegPlacement,
    mam_geometric_audit,
    read_image_dimensions,
)


class MamAuditTests(unittest.TestCase):
    def test_midpoint_delta_and_grid_export(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "audit.csv"
            rows = mam_geometric_audit(
                image_dimensions=(1000, 960),
                detected_pegs=[
                    PegPlacement(peg_id=1, x=300, y=480),
                    {"id": 2, "x": 400, "y": 482},
                ],
                config=MamAuditConfig(output_csv=str(output)),
            )

            self.assertEqual(rows[0]["Center_Axis_Delta"], 0.0)
            self.assertEqual(rows[1]["Center_Axis_Delta"], 2.0)
            self.assertEqual(rows[0]["Metric"], "Midpoint Accuracy Metric")
            self.assertEqual(rows[0]["Coordinate_Source"], "Reviewed Coordinate")
            self.assertTrue(output.exists())

            with output.open(newline="", encoding="utf-8") as csv_file:
                exported = list(csv.DictReader(csv_file))
            self.assertEqual(exported[1]["Peg_ID"], "2")
            self.assertEqual(exported[1]["Grid_Row"], "6")

    def test_png_dimensions_are_read_non_invasively(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = Path(tmpdir) / "workspace.png"
            image_path.write_bytes(
                b"\x89PNG\r\n\x1a\n"
                + b"\x00\x00\x00\rIHDR"
                + struct.pack(">II", 640, 480)
                + b"\x08\x02\x00\x00\x00"
            )

            self.assertEqual(read_image_dimensions(image_path), (640, 480))

    def test_out_of_bounds_pegs_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                mam_geometric_audit(
                    image_dimensions=(100, 100),
                    detected_pegs=[PegPlacement(peg_id=1, x=101, y=50)],
                    config=MamAuditConfig(output_csv=str(Path(tmpdir) / "audit.csv")),
                )


if __name__ == "__main__":
    unittest.main()
