"""
pipeline.py
===========
Orchestration engine – executes every step of the ASE Mapping &
Watermark workflow in order, with logging and report generation.

Usage
-----
    python src/pipeline.py --input fbd_object.json --owner "Alice" [--output report.json]

Steps executed
--------------
  1. Load FBD object file
  2. Map FBD blocks and resolve dependencies
  3. Generate cryptographic watermark
  4. Embed watermark into FBD metadata
  5. Verify watermark integrity
  6. Export watermarked FBD and write report
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Ensure src/ is on the path when executed directly
sys.path.insert(0, str(Path(__file__).parent))

from fbd_mapper import FBDObject, load_fbd, map_fbd
from watermark import embed_watermark, generate_watermark, verify_watermark

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class StepResult:
    step: int
    name: str
    status: str          # "ok" | "failed"
    duration_ms: float
    detail: str = ""


@dataclass
class PipelineReport:
    input_file: str
    owner: str
    steps: list[StepResult] = field(default_factory=list)
    success: bool = False
    output_file: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_file": self.input_file,
            "owner": self.owner,
            "success": self.success,
            "output_file": self.output_file,
            "steps": [
                {
                    "step": s.step,
                    "name": s.name,
                    "status": s.status,
                    "duration_ms": round(s.duration_ms, 3),
                    "detail": s.detail,
                }
                for s in self.steps
            ],
        }


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(
    input_path: str | Path,
    owner: str,
    output_path: str | Path | None = None,
    secret: str | None = None,
) -> PipelineReport:
    """
    Execute all pipeline steps and return a PipelineReport.

    Raises RuntimeError if any step fails.
    """
    input_path = Path(input_path)
    report = PipelineReport(input_file=str(input_path), owner=owner)

    fbd_data: dict[str, Any] = {}
    fbd_obj: FBDObject | None = None

    # ------------------------------------------------------------------
    # Step 1: Load
    # ------------------------------------------------------------------
    t0 = time.perf_counter()
    try:
        log.info("Step 1 – Loading FBD file: %s", input_path)
        fbd_data = load_fbd(input_path)
        elapsed = _ms(t0)
        report.steps.append(StepResult(1, "Load FBD file", "ok", elapsed,
                                        f"Loaded '{fbd_data.get('name')}'"))
        log.info("  ✓ Loaded FBD '%s' in %.1f ms", fbd_data.get("name"), elapsed)
    except Exception as exc:
        _fail(report, 1, "Load FBD file", t0, exc)

    # ------------------------------------------------------------------
    # Step 2: Map
    # ------------------------------------------------------------------
    t0 = time.perf_counter()
    try:
        log.info("Step 2 – Mapping FBD objects…")
        fbd_obj = map_fbd(fbd_data)
        elapsed = _ms(t0)
        dep_order = fbd_obj.metadata.get("dependency_order", [])
        report.steps.append(StepResult(2, "Map FBD objects", "ok", elapsed,
                                        f"{len(fbd_obj.blocks)} blocks, order={dep_order}"))
        log.info("  ✓ Mapped %d blocks in %.1f ms", len(fbd_obj.blocks), elapsed)
    except Exception as exc:
        _fail(report, 2, "Map FBD objects", t0, exc)

    # ------------------------------------------------------------------
    # Step 3: Generate watermark
    # ------------------------------------------------------------------
    t0 = time.perf_counter()
    try:
        log.info("Step 3 – Generating watermark for owner '%s'…", owner)
        watermark = generate_watermark(fbd_obj, owner=owner, secret=secret)
        elapsed = _ms(t0)
        report.steps.append(StepResult(3, "Generate watermark", "ok", elapsed,
                                        f"hash={watermark['hash'][:16]}…"))
        log.info("  ✓ Watermark generated in %.1f ms (hash=%s…)",
                 elapsed, watermark["hash"][:16])
    except Exception as exc:
        _fail(report, 3, "Generate watermark", t0, exc)

    # ------------------------------------------------------------------
    # Step 4: Embed watermark
    # ------------------------------------------------------------------
    t0 = time.perf_counter()
    try:
        log.info("Step 4 – Embedding watermark into FBD metadata…")
        embed_watermark(fbd_obj, watermark)
        elapsed = _ms(t0)
        report.steps.append(StepResult(4, "Embed watermark", "ok", elapsed))
        log.info("  ✓ Watermark embedded in %.1f ms", elapsed)
    except Exception as exc:
        _fail(report, 4, "Embed watermark", t0, exc)

    # ------------------------------------------------------------------
    # Step 5: Verify integrity
    # ------------------------------------------------------------------
    t0 = time.perf_counter()
    try:
        log.info("Step 5 – Verifying watermark integrity…")
        valid = verify_watermark(fbd_obj, secret=secret)
        elapsed = _ms(t0)
        if not valid:
            raise ValueError("Watermark integrity check failed")
        report.steps.append(StepResult(5, "Verify watermark", "ok", elapsed,
                                        "Integrity check passed"))
        log.info("  ✓ Integrity verified in %.1f ms", elapsed)
    except Exception as exc:
        _fail(report, 5, "Verify watermark", t0, exc)

    # ------------------------------------------------------------------
    # Step 6: Export
    # ------------------------------------------------------------------
    t0 = time.perf_counter()
    try:
        out = Path(output_path) if output_path else input_path.with_suffix(".watermarked.json")
        log.info("Step 6 – Exporting watermarked FBD to %s…", out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as fh:
            json.dump(fbd_obj.to_dict(), fh, indent=2)
        elapsed = _ms(t0)
        report.steps.append(StepResult(6, "Export watermarked FBD", "ok", elapsed,
                                        str(out)))
        report.output_file = str(out)
        log.info("  ✓ Exported to %s in %.1f ms", out, elapsed)
    except Exception as exc:
        _fail(report, 6, "Export watermarked FBD", t0, exc)

    report.success = True
    return report


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ms(t0: float) -> float:
    return (time.perf_counter() - t0) * 1000


def _fail(report: PipelineReport, step: int, name: str, t0: float,
          exc: Exception) -> None:
    elapsed = _ms(t0)
    msg = str(exc)
    report.steps.append(StepResult(step, name, "failed", elapsed, msg))
    log.error("  ✗ Step %d '%s' failed: %s", step, name, msg)
    raise RuntimeError(f"Pipeline aborted at step {step} ({name}): {msg}") from exc


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pipeline",
        description="ASE Mapping & Watermark pipeline for FBD objects",
    )
    parser.add_argument("--input", required=True, help="Path to input FBD JSON file")
    parser.add_argument("--owner", required=True, help="Owner/author name for watermark")
    parser.add_argument("--output", default=None, help="Path for watermarked output JSON")
    parser.add_argument("--report", default="pipeline_report.json",
                        help="Path to write the pipeline report (default: pipeline_report.json)")
    parser.add_argument("--secret", default=None,
                        help="HMAC secret for watermark signing (or set FBD_WATERMARK_SECRET env var)")
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    log.info("=" * 60)
    log.info("ASE Mapping & Watermark Pipeline – Starting")
    log.info("=" * 60)

    try:
        report = run_pipeline(
            input_path=args.input,
            owner=args.owner,
            output_path=args.output,
            secret=args.secret,
        )
    except RuntimeError as exc:
        log.error("Pipeline FAILED: %s", exc)
        sys.exit(1)

    # Write report
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as fh:
        json.dump(report.to_dict(), fh, indent=2)
    log.info("Report written to %s", report_path)

    log.info("=" * 60)
    log.info("Pipeline completed successfully ✓")
    log.info("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
