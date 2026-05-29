"""End-to-end conversion tests for demo missions and demo campaigns.

Covers:
- All demo .fsif files in missions/Demo_missions/ convert successfully.
- All demo .fcif files in campaigns/Demo_campaigns/ convert successfully.
- Output files are written to disk for each conversion.
"""

import sys
import tempfile
import unittest
from pathlib import Path

from fsif_to_fs2 import process_mission
from _fsif_test_helpers import SilencedTestCase, REPO_ROOT


class DemoConversionTesting(SilencedTestCase):

    def test_demo_missions_conversion(self):
        demo_missions_dir = REPO_ROOT / "missions" / "Demo_missions"
        self.assertTrue(
            demo_missions_dir.exists(),
            f"Demo missions directory not found: {demo_missions_dir}",
        )

        fsif_files = list(demo_missions_dir.glob("*.fsif"))
        self.assertTrue(len(fsif_files) > 0, "No demo missions found to test.")

        with tempfile.TemporaryDirectory() as tmpdir:
            for fsif_path in fsif_files:
                output_path = Path(tmpdir) / (fsif_path.stem + ".fs2")
                success = process_mission(
                    str(fsif_path),
                    str(output_path),
                    tts_settings={"enabled": True, "dry_run": True},
                )
                self.assertTrue(success, f"Failed to convert demo mission: {fsif_path.name}")
                self.assertTrue(
                    output_path.exists(),
                    f"Output file not generated for: {fsif_path.name}",
                )

    def test_demo_campaigns_conversion(self):
        demo_campaigns_dir = REPO_ROOT / "campaigns" / "Demo_campaigns"
        self.assertTrue(
            demo_campaigns_dir.exists(),
            f"Demo campaigns directory not found: {demo_campaigns_dir}",
        )

        fcif_files = list(demo_campaigns_dir.glob("*.fcif"))
        self.assertTrue(len(fcif_files) > 0, "No demo campaigns found to test.")

        fcif_dir = REPO_ROOT / "FCIF_to_FC2_Converter"
        if str(fcif_dir) not in sys.path:
            sys.path.insert(0, str(fcif_dir))
        from fcif_to_fc2 import process_campaign

        with tempfile.TemporaryDirectory() as tmpdir:
            for fcif_path in fcif_files:
                output_path = Path(tmpdir) / (fcif_path.stem + ".fc2")
                success = process_campaign(str(fcif_path), str(output_path))
                self.assertTrue(success, f"Failed to convert demo campaign: {fcif_path.name}")
                self.assertTrue(
                    output_path.exists(),
                    f"Output file not generated for: {fcif_path.name}",
                )


if __name__ == "__main__":
    unittest.main()
