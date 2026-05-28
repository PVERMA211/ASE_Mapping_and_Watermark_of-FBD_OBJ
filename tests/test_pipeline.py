"""
test_pipeline.py
================
Unit tests for the ASE Mapping & Watermark pipeline.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

# Put src/ on the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fbd_mapper import FBDObject, load_fbd, map_fbd
from watermark import embed_watermark, generate_watermark, verify_watermark
from pipeline import PipelineReport, StepResult, run_pipeline


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_FBD = {
    "name": "TestDiagram",
    "blocks": [
        {"id": "B1", "type": "AND", "inputs": ["I1", "I2"], "output": "O1"},
        {"id": "B2", "type": "OR",  "inputs": ["I3"],        "output": "O2"},
        {"id": "B3", "type": "NOT", "inputs": ["I4"],        "output": "O3"},
    ],
    "connections": [
        {"from": "B1.O1", "to": "B2.I3"},
        {"from": "B2.O2", "to": "B3.I4"},
    ],
}


@pytest.fixture()
def fbd_file(tmp_path: Path) -> Path:
    p = tmp_path / "sample.json"
    p.write_text(json.dumps(SAMPLE_FBD))
    return p


@pytest.fixture()
def mapped_fbd() -> FBDObject:
    return map_fbd(SAMPLE_FBD)


# ---------------------------------------------------------------------------
# fbd_mapper tests
# ---------------------------------------------------------------------------

class TestLoadFBD:
    def test_loads_valid_file(self, fbd_file: Path) -> None:
        data = load_fbd(fbd_file)
        assert data["name"] == "TestDiagram"
        assert len(data["blocks"]) == 3

    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_fbd(tmp_path / "nonexistent.json")

    def test_raises_on_missing_required_key(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps({"blocks": []}))
        with pytest.raises(ValueError, match="missing required keys"):
            load_fbd(bad)


class TestMapFBD:
    def test_creates_correct_number_of_blocks(self, mapped_fbd: FBDObject) -> None:
        assert len(mapped_fbd.blocks) == 3

    def test_assigns_uids(self, mapped_fbd: FBDObject) -> None:
        for block in mapped_fbd.blocks:
            assert block.uid, "Block should have a UUID"

    def test_dependency_order_in_metadata(self, mapped_fbd: FBDObject) -> None:
        order = mapped_fbd.metadata["dependency_order"]
        assert isinstance(order, list)
        assert len(order) == 3

    def test_dependency_order_respects_connections(self, mapped_fbd: FBDObject) -> None:
        order = mapped_fbd.metadata["dependency_order"]
        # B1 must come before B2, B2 before B3
        assert order.index("B1") < order.index("B2")
        assert order.index("B2") < order.index("B3")

    def test_cycle_raises_value_error(self) -> None:
        cyclic = {
            "name": "Cyclic",
            "blocks": [
                {"id": "B1", "type": "AND", "inputs": [], "output": "O1"},
                {"id": "B2", "type": "AND", "inputs": [], "output": "O2"},
            ],
            "connections": [
                {"from": "B1.O1", "to": "B2.I1"},
                {"from": "B2.O2", "to": "B1.I1"},
            ],
        }
        with pytest.raises(ValueError, match="Cycle detected"):
            map_fbd(cyclic)


# ---------------------------------------------------------------------------
# watermark tests
# ---------------------------------------------------------------------------

class TestWatermark:
    SECRET = "test-secret-key"

    def test_generate_returns_required_keys(self, mapped_fbd: FBDObject) -> None:
        wm = generate_watermark(mapped_fbd, owner="Alice", secret=self.SECRET)
        assert {"owner", "timestamp", "hash", "signature"} == wm.keys()

    def test_owner_stored_correctly(self, mapped_fbd: FBDObject) -> None:
        wm = generate_watermark(mapped_fbd, owner="Alice", secret=self.SECRET)
        assert wm["owner"] == "Alice"

    def test_embed_and_verify(self, mapped_fbd: FBDObject) -> None:
        wm = generate_watermark(mapped_fbd, owner="Alice", secret=self.SECRET)
        embed_watermark(mapped_fbd, wm)
        assert verify_watermark(mapped_fbd, secret=self.SECRET)

    def test_tampered_content_fails_verification(self, mapped_fbd: FBDObject) -> None:
        wm = generate_watermark(mapped_fbd, owner="Alice", secret=self.SECRET)
        embed_watermark(mapped_fbd, wm)
        # Tamper: rename a block
        mapped_fbd.blocks[0].block_id = "TAMPERED"
        assert not verify_watermark(mapped_fbd, secret=self.SECRET)

    def test_wrong_secret_fails_verification(self, mapped_fbd: FBDObject) -> None:
        wm = generate_watermark(mapped_fbd, owner="Alice", secret=self.SECRET)
        embed_watermark(mapped_fbd, wm)
        assert not verify_watermark(mapped_fbd, secret="wrong-secret")

    def test_missing_watermark_raises_key_error(self, mapped_fbd: FBDObject) -> None:
        with pytest.raises(KeyError):
            verify_watermark(mapped_fbd, secret=self.SECRET)


# ---------------------------------------------------------------------------
# pipeline tests
# ---------------------------------------------------------------------------

class TestRunPipeline:
    SECRET = "pipeline-test-secret"

    def test_full_pipeline_succeeds(self, fbd_file: Path, tmp_path: Path) -> None:
        report = run_pipeline(
            input_path=fbd_file,
            owner="TestOwner",
            output_path=tmp_path / "out.json",
            secret=self.SECRET,
        )
        assert report.success
        assert len(report.steps) == 6
        assert all(s.status == "ok" for s in report.steps)

    def test_output_file_is_valid_json(self, fbd_file: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.json"
        run_pipeline(fbd_file, owner="TestOwner", output_path=out, secret=self.SECRET)
        data = json.loads(out.read_text())
        assert "watermark" in data["metadata"]

    def test_pipeline_fails_on_bad_input(self, tmp_path: Path) -> None:
        with pytest.raises(RuntimeError, match="step 1"):
            run_pipeline(tmp_path / "ghost.json", owner="X", secret=self.SECRET)

    def test_report_has_all_step_names(self, fbd_file: Path, tmp_path: Path) -> None:
        report = run_pipeline(fbd_file, owner="X", output_path=tmp_path / "o.json",
                              secret=self.SECRET)
        names = [s.name for s in report.steps]
        assert "Load FBD file" in names
        assert "Map FBD objects" in names
        assert "Generate watermark" in names
        assert "Embed watermark" in names
        assert "Verify watermark" in names
        assert "Export watermarked FBD" in names
