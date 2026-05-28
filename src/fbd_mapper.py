"""
fbd_mapper.py
=============
Step 1 & 2 – Load, parse, and map FBD (Function Block Diagram) objects.

An FBD object is represented as a JSON document with the following schema:

{
    "name": "MyDiagram",
    "blocks": [
        {"id": "B1", "type": "AND", "inputs": ["I1", "I2"], "output": "O1"},
        ...
    ],
    "connections": [
        {"from": "B1.O1", "to": "B2.I1"},
        ...
    ]
}
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class FBDBlock:
    """Represents a single functional block in the diagram."""

    block_id: str
    block_type: str
    inputs: list[str]
    output: str
    uid: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict[str, Any]:
        return {
            "block_id": self.block_id,
            "block_type": self.block_type,
            "inputs": self.inputs,
            "output": self.output,
            "uid": self.uid,
        }


@dataclass
class FBDConnection:
    """Directed connection between two block ports."""

    source: str
    target: str

    def to_dict(self) -> dict[str, str]:
        return {"from": self.source, "to": self.target}


@dataclass
class FBDObject:
    """Top-level container for a parsed and mapped FBD diagram."""

    name: str
    blocks: list[FBDBlock] = field(default_factory=list)
    connections: list[FBDConnection] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "blocks": [b.to_dict() for b in self.blocks],
            "connections": [c.to_dict() for c in self.connections],
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_fbd(path: str | Path) -> dict[str, Any]:
    """Load a raw FBD JSON file and return the parsed dict."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"FBD file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    _validate_schema(data)
    return data


def map_fbd(raw: dict[str, Any]) -> FBDObject:
    """
    Map raw FBD data into a typed FBDObject.

    - Assigns a stable UUID to every block (idempotent: preserves existing UIDs).
    - Resolves and records inter-block dependency order.
    """
    blocks: list[FBDBlock] = []
    for raw_block in raw.get("blocks", []):
        block = FBDBlock(
            block_id=raw_block["id"],
            block_type=raw_block["type"],
            inputs=list(raw_block.get("inputs", [])),
            output=raw_block.get("output", ""),
            uid=raw_block.get("uid", str(uuid.uuid4())),
        )
        blocks.append(block)

    connections: list[FBDConnection] = [
        FBDConnection(source=c["from"], target=c["to"])
        for c in raw.get("connections", [])
    ]

    fbd = FBDObject(
        name=raw["name"],
        blocks=blocks,
        connections=connections,
        metadata=dict(raw.get("metadata", {})),
    )
    fbd.metadata["dependency_order"] = _resolve_dependency_order(fbd)
    return fbd


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validate_schema(data: dict[str, Any]) -> None:
    required = {"name", "blocks"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"FBD schema missing required keys: {missing}")
    if not isinstance(data["blocks"], list):
        raise TypeError("'blocks' must be a list")


def _resolve_dependency_order(fbd: FBDObject) -> list[str]:
    """
    Return blocks in topological order based on connections.
    Raises ValueError on cycles.
    """
    # Build adjacency: target_block depends on source_block
    graph: dict[str, set[str]] = {b.block_id: set() for b in fbd.blocks}
    for conn in fbd.connections:
        src_block = conn.source.split(".")[0]
        tgt_block = conn.target.split(".")[0]
        if tgt_block in graph:
            graph[tgt_block].add(src_block)

    visited: set[str] = set()
    in_stack: set[str] = set()
    order: list[str] = []

    def _visit(node: str) -> None:
        if node in in_stack:
            raise ValueError(f"Cycle detected at block '{node}'")
        if node in visited:
            return
        in_stack.add(node)
        for dep in graph.get(node, set()):
            _visit(dep)
        in_stack.discard(node)
        visited.add(node)
        order.append(node)

    for block_id in list(graph):
        _visit(block_id)

    return order
