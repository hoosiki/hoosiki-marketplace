"""Tests for the conflict-aware wave scheduler.

The bug this scheduler exists to prevent: two features with no dependency
between them were made sibling waves and ran concurrently while editing the
same files, so the stage merge failed. Every test here is a property of that
failure or of the guardrails around it.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = (Path(__file__).resolve().parents[1] / "plugins" / "lazy2work" / "skills"
          / "generate-optimized-spec-kit-prompt" / "assets" / "speckit_waves.py")


def write_case(tmp_path, features, impacts):
    (tmp_path / ".impact").mkdir(parents=True, exist_ok=True)
    (tmp_path / "waves.json").write_text(
        json.dumps({"project": "t", "features": features}), encoding="utf-8")
    for fid, payload in impacts.items():
        base = {"feature": fid, "status": "ok", "creates": [], "modifies": [],
                "tests": [], "docs_configs": [], "registries": [],
                "completeness_claims": [], "extends_sets": []}
        base.update(payload)
        (tmp_path / ".impact" / f"{fid}.json").write_text(
            json.dumps(base), encoding="utf-8")


def run(tmp_path, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp_path), "--no-augment", *args],
        capture_output=True, text=True)


def placement(tmp_path):
    doc = json.loads((tmp_path / "waves.json").read_text(encoding="utf-8"))
    return {f: (w["name"], w["stage"]) for w in doc["waves"] for f in w["features"]}, doc


def siblings(loc, a, b):
    """True when a and b run concurrently: different waves, same stage."""
    return loc[a][0] != loc[b][0] and loc[a][1] == loc[b][1]


def two_leaves(extra_a=None, extra_b=None):
    features = [
        {"id": "000-base", "effective_blocked_by": []},
        {"id": "001-a", "effective_blocked_by": ["000-base"]},
        {"id": "002-b", "effective_blocked_by": ["000-base"]},
    ]
    impacts = {
        "000-base": {"modifies": [{"path": "app/core.py"}]},
        "001-a": {"modifies": [{"path": "app/a.py"}]},
        "002-b": {"modifies": [{"path": "app/b.py"}]},
    }
    if extra_a:
        impacts["001-a"].update(extra_a)
    if extra_b:
        impacts["002-b"].update(extra_b)
    return features, impacts


def test_independent_features_stay_siblings(tmp_path):
    """No overlap must not cost parallelism."""
    features, impacts = two_leaves()
    # Distinct directories, so not even the same-module signal fires.
    impacts["001-a"]["modifies"] = [{"path": "app/alpha/a.py"}]
    impacts["002-b"]["modifies"] = [{"path": "app/beta/b.py"}]
    write_case(tmp_path, features, impacts)
    assert run(tmp_path).returncode == 0
    loc, _ = placement(tmp_path)
    assert siblings(loc, "001-a", "002-b")


def test_strong_shared_file_prevents_siblings(tmp_path):
    """The original bug: a shared logic file must break the sibling relation."""
    features, impacts = two_leaves(
        extra_a={"modifies": [{"path": "app/services.py"}]},
        extra_b={"modifies": [{"path": "app/services.py"}]})
    write_case(tmp_path, features, impacts)
    assert run(tmp_path).returncode == 0
    loc, _ = placement(tmp_path)
    assert not siblings(loc, "001-a", "002-b")


def test_additive_registry_does_not_serialise(tmp_path):
    """Append-only files are handled by ownership, not by killing parallelism."""
    features, impacts = two_leaves()
    impacts["001-a"] = {"modifies": [{"path": "app/alpha/a.py"}],
                        "registries": [{"path": "config/settings.py"}]}
    impacts["002-b"] = {"modifies": [{"path": "app/beta/b.py"}],
                        "registries": [{"path": "config/settings.py"}]}
    write_case(tmp_path, features, impacts)
    assert run(tmp_path).returncode == 0
    loc, _ = placement(tmp_path)
    assert siblings(loc, "001-a", "002-b")


def test_completeness_claim_prevents_siblings_without_shared_files(tmp_path):
    """The conflict file overlap cannot see: a clean merge that breaks a test."""
    features, impacts = two_leaves(
        extra_a={"completeness_claims": [{"set": "verdict.consumers"}]},
        extra_b={"extends_sets": [{"set": "verdict.consumers"}]})
    impacts["001-a"]["modifies"] = [{"path": "app/alpha/a.py"}]
    impacts["002-b"]["modifies"] = [{"path": "app/beta/b.py"}]
    write_case(tmp_path, features, impacts)
    assert run(tmp_path).returncode == 0
    loc, _ = placement(tmp_path)
    assert not siblings(loc, "001-a", "002-b")


def test_missing_prediction_is_refused(tmp_path):
    """Absent data is not the same as no overlap, so the run stops."""
    features, impacts = two_leaves()
    del impacts["002-b"]
    write_case(tmp_path, features, impacts)
    res = run(tmp_path)
    assert res.returncode == 2
    assert "002-b" in res.stderr


def test_failed_prediction_is_refused(tmp_path):
    features, impacts = two_leaves()
    impacts["002-b"] = {"status": "failed", "error": "timeout"}
    write_case(tmp_path, features, impacts)
    assert run(tmp_path).returncode == 2


def test_force_trunk_serialises_and_keeps_precedence(tmp_path):
    """An unpredicted feature is serialised, never silently treated as disjoint."""
    features, impacts = two_leaves()
    del impacts["002-b"]
    write_case(tmp_path, features, impacts)
    assert run(tmp_path, "--force-trunk").returncode == 0
    loc, doc = placement(tmp_path)
    assert not siblings(loc, "001-a", "002-b")
    marks = {f["id"]: f["placement"] for f in doc["features"]}
    assert marks["002-b"] == "unpredicted"
    # 000-base blocks both, so it must never land in a later stage than them.
    assert loc["000-base"][1] <= min(loc["001-a"][1], loc["002-b"][1])


def test_status_and_schema_are_stamped(tmp_path):
    features, impacts = two_leaves()
    write_case(tmp_path, features, impacts)
    run(tmp_path)
    doc = json.loads((tmp_path / "waves.json").read_text(encoding="utf-8"))
    assert doc["status"] == "provisional" and "finalized_at" not in doc
    run(tmp_path, "--status", "final")
    doc = json.loads((tmp_path / "waves.json").read_text(encoding="utf-8"))
    assert doc["status"] == "final" and doc["schema"] == 3 and "finalized_at" in doc


def test_conflict_graph_is_written_with_provenance(tmp_path):
    features, impacts = two_leaves(
        extra_a={"modifies": [{"path": "app/services.py"}]},
        extra_b={"modifies": [{"path": "app/services.py"}]})
    write_case(tmp_path, features, impacts)
    run(tmp_path)
    graph = json.loads((tmp_path / "conflict-graph.json").read_text(encoding="utf-8"))
    strong = [e for e in graph["edges"] if e["grade"] == "strong"]
    assert any("app/services.py" in e["files"] for e in strong)
    assert graph["makespan"]["after_repair"] >= graph["makespan"]["before_repair"]


def test_blocker_never_lands_after_its_dependent(tmp_path):
    """A chain must stay ordered no matter how the repair pass moves waves."""
    features = [
        {"id": "000-base", "effective_blocked_by": []},
        {"id": "001-mid", "effective_blocked_by": ["000-base"]},
        {"id": "002-leaf", "effective_blocked_by": ["001-mid"]},
        {"id": "003-other", "effective_blocked_by": ["000-base"]},
    ]
    impacts = {
        "000-base": {"modifies": [{"path": "app/core.py"}]},
        "001-mid": {"modifies": [{"path": "app/shared.py"}]},
        "002-leaf": {"modifies": [{"path": "app/leaf.py"}]},
        "003-other": {"modifies": [{"path": "app/shared.py"}]},
    }
    write_case(tmp_path, features, impacts)
    assert run(tmp_path).returncode == 0
    loc, doc = placement(tmp_path)
    # Position *within* a wave, so same-wave ordering is actually asserted.
    pos = {f: i for w in doc["waves"] for i, f in enumerate(w["features"])}
    for feat in doc["features"]:
        fid = feat["id"]
        for dep in feat["effective_blocked_by"]:
            if loc[dep][0] == loc[fid][0]:
                assert pos[dep] < pos[fid], f"{dep} must precede {fid} in the wave"
            else:
                assert loc[dep][1] < loc[fid][1], f"{dep} must be in an earlier stage than {fid}"
