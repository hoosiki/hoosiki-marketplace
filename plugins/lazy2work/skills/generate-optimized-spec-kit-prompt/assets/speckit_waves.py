#!/usr/bin/env python3
"""Compute the stage/wave plan from per-feature impact predictions.

Waves are dependency *chains*. A strong conflict means two features may not be
**siblings** — that is satisfied either by putting them in the same wave (they
run sequentially in one worktree, where an overlap is harmless) or by putting
them in different stages. This script picks whichever costs less wall-clock.

Inputs
  <prompts>/waves.json          features[] with ids + effective_blocked_by
  <prompts>/.impact/*.json      one impact prediction per feature
  <prompts>/conflict-policy.toml  optional grading overrides

Outputs
  <prompts>/waves.json          waves[]/stages[]/hotspots[]/status rewritten
  <prompts>/conflict-graph.json edges, grades, hubs, provenance

Exit codes
  0 ok   1 usage/IO error   2 refused (failed predictions, see --force-trunk)
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import subprocess
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    tomllib = None

STRONG, CONDITIONAL, ADDITIVE = "strong", "conditional", "additive"
RANK = {ADDITIVE: 0, CONDITIONAL: 1, STRONG: 2}

# Grades are deliberately conservative: prevention beats parallelism, and a tie
# resolves upward. Projects relax this in conflict-policy.toml.
DEFAULT_POLICY = {
    "hub_threshold": 3,
    "additive": [
        "**/settings.py", "**/settings/*.py", "**/urls.py", "**/*_urls.py",
        "**/api_router.py", "**/migrations/**", "**/locale/**", "**/*.po",
        "pyproject.toml", "uv.lock", "package.json", "package-lock.json",
        "requirements/*.txt", ".env.example", "**/__init__.py",
    ],
    "strong": [
        "**/models.py", "**/services.py", "**/views.py", "**/forms.py",
        "**/admin.py", "**/serializers.py", "**/tests/**", "**/test_*.py",
        "**/*_test.py", "**/conftest.py",
    ],
    "conditional": ["**/*.md", "**/*.rst", "**/*.txt", "**/*.yaml", "**/*.yml"],
    # Unmatched source files fall through to this.
    "default_source": STRONG,
    "default_other": CONDITIONAL,
    "source_suffixes": [".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".rb", ".html"],
}

CATEGORIES = ("creates", "modifies", "tests", "docs_configs", "registries")
# A category can force a grade floor regardless of path.
CATEGORY_FLOOR = {"registries": ADDITIVE, "tests": STRONG}


# ---------------------------------------------------------------- utilities

def die(msg: str, code: int = 1):
    print(f"✗ {msg}", file=sys.stderr)
    sys.exit(code)


def norm(path: str) -> str:
    p = (path or "").strip().replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p.strip("/")


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        die(f"{path}: {exc}")


def load_policy(prompts: Path, explicit: str | None) -> dict:
    pol = dict(DEFAULT_POLICY)
    candidate = Path(explicit) if explicit else prompts / "conflict-policy.toml"
    if not candidate.exists():
        return pol
    if tomllib is None:
        print(f"⚠ {candidate} ignored — Python 3.11+ needed for tomllib", file=sys.stderr)
        return pol
    try:
        raw = tomllib.loads(candidate.read_text(encoding="utf-8"))
    except Exception as exc:
        die(f"{candidate}: {exc}")
    grades = raw.get("grades", {})
    for key in (ADDITIVE, STRONG, CONDITIONAL):
        if key in grades:
            # Project patterns take precedence; keep defaults as the tail.
            pol[key] = list(grades[key]) + pol[key]
    for key in ("hub_threshold", "default_source", "default_other"):
        if key in raw:
            pol[key] = raw[key]
    return pol


def grade_of(path: str, category: str, policy: dict) -> str:
    floor = CATEGORY_FLOOR.get(category)
    # Explicit patterns win over the category floor, most-specific list first.
    for key in (ADDITIVE, STRONG, CONDITIONAL):
        for pat in policy.get(key, []):
            if fnmatch.fnmatch(path, pat) or fnmatch.fnmatch("/" + path, pat):
                return key
    if floor:
        return floor
    suffix = os.path.splitext(path)[1]
    if suffix in policy["source_suffixes"]:
        return policy["default_source"]
    return policy["default_other"]


def run(cmd: list[str], cwd: Path) -> str:
    try:
        out = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=90)
        return out.stdout if out.returncode == 0 else ""
    except Exception:
        return ""


# ---------------------------------------------------------------- inputs

def read_impacts(prompts: Path, feature_ids: list[str]) -> tuple[dict, list[str]]:
    """Return {feature_id: impact} and the list of features with no usable prediction."""
    impact_dir = prompts / ".impact"
    impacts, missing = {}, []
    for fid in feature_ids:
        path = impact_dir / f"{fid}.json"
        if not path.exists():
            missing.append(fid)
            continue
        data = load_json(path)
        if data.get("status") == "failed":
            missing.append(fid)
            continue
        impacts[fid] = data
    return impacts, missing


def paths_of(impact: dict) -> list[tuple[str, str, float]]:
    """Flatten an impact record into (path, category, confidence)."""
    out = []
    for cat in CATEGORIES:
        for entry in impact.get(cat, []) or []:
            if isinstance(entry, str):
                p, conf = entry, 1.0
            else:
                p, conf = entry.get("path", ""), float(entry.get("confidence", 1.0))
            p = norm(p)
            if p:
                out.append((p, cat, conf))
    return out


def symbols_of(impact: dict) -> list[str]:
    syms = set()
    for cat in CATEGORIES:
        for entry in impact.get(cat, []) or []:
            if isinstance(entry, dict):
                for s in entry.get("symbols", []) or []:
                    if isinstance(s, str) and len(s) >= 4:
                        syms.add(s)
    for s in impact.get("symbols", []) or []:
        if isinstance(s, str) and len(s) >= 4:
            syms.add(s)
    return sorted(syms)


# ---------------------------------------------------------------- augmentation

def augment_grep(repo: Path, impacts: dict, feature_paths: dict) -> int:
    """M1 — reverse references. A symbol a feature touches pulls in its consumers."""
    added = 0
    for fid, impact in impacts.items():
        for sym in symbols_of(impact):
            out = run(["git", "grep", "-l", "-F", "--", sym], repo)
            for line in out.splitlines():
                p = norm(line)
                if p and p not in feature_paths[fid]:
                    feature_paths[fid][p] = {"category": "modifies", "confidence": 0.5,
                                             "source": f"grep:{sym}"}
                    added += 1
    return added


def augment_cochange(repo: Path, feature_paths: dict, window: int = 400,
                     ratio: float = 0.5, cap: int = 5) -> int:
    """M2 — logical coupling. Files that historically move together will again."""
    log = run(["git", "log", f"-{window}", "--name-only", "--pretty=format:%H"], repo)
    if not log:
        return 0
    commits, current = [], set()
    for line in log.splitlines():
        line = line.strip()
        if not line:
            continue
        if len(line) == 40 and all(c in "0123456789abcdef" for c in line):
            if current:
                commits.append(current)
            current = set()
        else:
            current.add(norm(line))
    if current:
        commits.append(current)

    touches = defaultdict(int)
    pair = defaultdict(int)
    for files in commits:
        for f in files:
            touches[f] += 1
        for a, b in combinations(sorted(files), 2):
            pair[(a, b)] += 1

    coupled = defaultdict(list)
    for (a, b), n in pair.items():
        for src, dst in ((a, b), (b, a)):
            if touches[src] and n / touches[src] >= ratio:
                coupled[src].append((n, dst))
    for src in coupled:
        coupled[src].sort(reverse=True)

    added = 0
    for fid, paths in feature_paths.items():
        for seed in list(paths):
            for _, dst in coupled.get(seed, [])[:cap]:
                if dst not in paths:
                    paths[dst] = {"category": "modifies", "confidence": 0.4,
                                  "source": f"cochange:{seed}"}
                    added += 1
    return added


# ---------------------------------------------------------------- graphs

def build_conflict_graph(feature_paths: dict, impacts: dict, policy: dict):
    """Return (edges, hubs, owners). An edge is (a, b) -> {grade, files, reasons}."""
    holders = defaultdict(set)
    for fid, paths in feature_paths.items():
        for p in paths:
            holders[p].add(fid)

    hub_threshold = int(policy.get("hub_threshold", 3))
    hubs, owners = [], {}
    for p, fids in sorted(holders.items()):
        if len(fids) < 2:
            continue
        grades = {grade_of(p, feature_paths[f][p]["category"], policy) for f in fids}
        grade = max(grades, key=lambda g: RANK[g])
        if grade == ADDITIVE:
            owners[p] = sorted(fids)[0]
        if len(fids) >= hub_threshold:
            hubs.append({"path": p, "touched_by": sorted(fids), "grade": grade,
                         "owner": owners.get(p),
                         "note": "additive — owner + idempotent edit" if grade == ADDITIVE
                                 else "logic hub — consider moving ownership into the trunk"})

    edges = {}

    def add_edge(a, b, grade, fileref, reason):
        key = tuple(sorted((a, b)))
        e = edges.setdefault(key, {"grade": ADDITIVE, "files": [], "reasons": []})
        if RANK[grade] > RANK[e["grade"]]:
            e["grade"] = grade
        if fileref and fileref not in e["files"]:
            e["files"].append(fileref)
        if reason and reason not in e["reasons"]:
            e["reasons"].append(reason)

    # Shared paths.
    for p, fids in holders.items():
        if len(fids) < 2:
            continue
        for a, b in combinations(sorted(fids), 2):
            ga = grade_of(p, feature_paths[a][p]["category"], policy)
            gb = grade_of(p, feature_paths[b][p]["category"], policy)
            grade = max((ga, gb), key=lambda g: RANK[g])
            if grade == ADDITIVE:
                continue  # owner + idempotency rule handles it
            add_edge(a, b, grade, p, f"shared {grade} file")

    # Same-directory overlap without a shared file — the MVC-slice signal.
    dirs = defaultdict(set)
    for fid, paths in feature_paths.items():
        for p in paths:
            if grade_of(p, paths[p]["category"], policy) == ADDITIVE:
                continue
            d = os.path.dirname(p)
            if d:
                dirs[d].add(fid)
    for d, fids in dirs.items():
        if len(fids) < 2:
            continue
        for a, b in combinations(sorted(fids), 2):
            key = tuple(sorted((a, b)))
            if key in edges:
                continue
            add_edge(a, b, CONDITIONAL, d + "/", "same module directory")

    # Completeness claim vs set extension — invisible to file overlap.
    claims = defaultdict(set)
    extends = defaultdict(set)
    for fid, impact in impacts.items():
        for c in impact.get("completeness_claims", []) or []:
            name = c.get("set") if isinstance(c, dict) else c
            if name:
                claims[str(name).strip()].add(fid)
        for c in impact.get("extends_sets", []) or []:
            name = c.get("set") if isinstance(c, dict) else c
            if name:
                extends[str(name).strip()].add(fid)
    completeness_pairs = []
    for name, claimants in claims.items():
        for extender in extends.get(name, set()):
            for claimant in claimants:
                if claimant == extender:
                    continue
                add_edge(claimant, extender, STRONG, None,
                         f"completeness claim '{name}' extended")
                completeness_pairs.append({"set": name, "claimant": claimant,
                                           "extender": extender})

    return edges, hubs, owners, completeness_pairs


def transitive(nodes, succ):
    reach = {n: set() for n in nodes}
    for n in reversed(list(topo_order(nodes, succ))):
        acc = set()
        for m in succ.get(n, ()):
            acc.add(m)
            acc |= reach[m]
        reach[n] = acc
    return reach


def topo_order(nodes, succ):
    indeg = {n: 0 for n in nodes}
    for n in nodes:
        for m in succ.get(n, ()):
            indeg[m] += 1
    ready = sorted([n for n in nodes if indeg[n] == 0])
    out = []
    while ready:
        n = ready.pop(0)
        out.append(n)
        for m in sorted(succ.get(n, ())):
            indeg[m] -= 1
            if indeg[m] == 0:
                ready.append(m)
                ready.sort()
    if len(out) != len(nodes):
        die("dependency cycle in effective_blocked_by")
    return out


# ---------------------------------------------------------------- scheduling

def spine_partition(nodes, succ, pred):
    """Existing behaviour: spine -> trunk waves, gap components -> branch waves."""
    order = topo_order(nodes, succ)
    desc = transitive(nodes, succ)
    anc = transitive(nodes, pred)
    total = len(nodes)
    spine = {n for n in nodes if len(desc[n] | anc[n]) + 1 == total}

    groups, current, kind = [], [], None
    for n in order:
        k = "trunk" if n in spine else "branch"
        if kind is None or k == kind:
            current.append(n)
            kind = k
        else:
            groups.append((kind, current))
            current, kind = [n], k
    if current:
        groups.append((kind, current))

    stages = []
    for k, members in groups:
        if k == "trunk":
            stages.append([members])
            continue
        # Split the gap into weakly connected components.
        adj = defaultdict(set)
        member_set = set(members)
        for n in members:
            for m in list(succ.get(n, ())) + list(pred.get(n, ())):
                if m in member_set:
                    adj[n].add(m)
                    adj[m].add(n)
        seen, comps = set(), []
        for n in members:
            if n in seen:
                continue
            stack, comp = [n], []
            seen.add(n)
            while stack:
                cur = stack.pop()
                comp.append(cur)
                for m in adj.get(cur, ()):
                    if m not in seen:
                        seen.add(m)
                        stack.append(m)
            comps.append([x for x in order if x in set(comp)])
        stages.append(comps)
    return stages


def makespan(stages):
    return sum(max((len(w) for w in st), default=0) for st in stages)


def violations(stages, edges):
    """Strong edges crossing sibling waves inside one stage."""
    bad = []
    for si, st in enumerate(stages):
        where = {}
        for wi, wave in enumerate(st):
            for f in wave:
                where[f] = wi
        for (a, b), e in edges.items():
            if e["grade"] != STRONG:
                continue
            if a in where and b in where and where[a] != where[b]:
                bad.append((si, where[a], where[b], a, b))
    return bad


def respects_precedence(stages, succ):
    """A blocker must be earlier in the same wave or in an earlier stage."""
    pos = {}
    for si, st in enumerate(stages):
        for wi, wave in enumerate(st):
            for idx, f in enumerate(wave):
                pos[f] = (si, wi, idx)
    for n, targets in succ.items():
        if n not in pos:
            continue
        for m in targets:
            if m not in pos:
                continue
            sn, wn, i_n = pos[n]
            sm, wm, i_m = pos[m]
            if sm > sn:
                continue
            if sm == sn and wm == wn and i_m > i_n:
                continue
            return False
    return True


def merge_waves(stages, si, wi, wj, order_index):
    new = [list(w) for w in stages[si]]
    combined = new[wi] + new[wj]
    combined.sort(key=lambda f: order_index[f])
    keep = [w for k, w in enumerate(new) if k not in (wi, wj)]
    keep.insert(min(wi, wj), combined)
    out = [list(s) for s in stages]
    out[si] = keep
    return out


def split_stage(stages, si, wj):
    new = [list(w) for w in stages[si]]
    moved = new.pop(wj)
    out = [list(s) for s in stages]
    if new:
        out[si] = new
        out.insert(si + 1, [moved])
    else:
        out[si] = [moved]
    return out


def repair(stages, edges, succ, order_index, max_iter=200):
    """Resolve every strong sibling violation, preferring the cheaper fix."""
    log = []
    for _ in range(max_iter):
        bad = violations(stages, edges)
        if not bad:
            return stages, log
        si, wi, wj, a, b = bad[0]
        cand = []
        merged = merge_waves(stages, si, wi, wj, order_index)
        if respects_precedence(merged, succ):
            cand.append(("merge", makespan(merged), merged))
        split = split_stage(stages, si, max(wi, wj))
        if respects_precedence(split, succ):
            cand.append(("split", makespan(split), split))
        if not cand:
            die(f"cannot separate {a} and {b} without breaking precedence")
        cand.sort(key=lambda c: (c[1], c[0] != "merge"))
        action, cost, stages = cand[0]
        log.append({"action": action, "features": [a, b], "makespan": cost})
    die("wave repair did not converge")


# ---------------------------------------------------------------- naming

def name_wave(features, kind, index, meta):
    slugs = []
    for f in features:
        parts = f.split("-", 1)
        slugs.append(parts[1] if len(parts) > 1 else f)
    theme = slugs[0] if slugs else f"wave{index}"
    theme = "-".join(theme.split("-")[:2])
    return {
        "name": f"w{index}-{theme}",
        "title": meta.get(features[0], {}).get("title") or theme.replace("-", " ").title(),
        "kind": kind,
        "features": features,
    }


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description="Compute the conflict-aware wave plan.")
    ap.add_argument("prompts", help=".speckit-prompts/{prd-name}")
    ap.add_argument("--policy")
    ap.add_argument("--status", choices=["provisional", "final"], default="provisional")
    ap.add_argument("--repo")
    ap.add_argument("--force-trunk", action="store_true",
                    help="place features whose prediction failed into the trunk instead of refusing")
    ap.add_argument("--no-augment", action="store_true", help="skip grep and co-change augmentation")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    prompts = Path(args.prompts).resolve()
    if not prompts.is_dir():
        die(f"no such prompts directory: {prompts}")
    waves_path = prompts / "waves.json"
    if not waves_path.exists():
        die(f"{waves_path} not found — the skill writes features[] before scheduling")
    doc = load_json(waves_path)

    features = doc.get("features") or []
    if not features:
        die("waves.json has no features[]")
    meta = {f["id"]: f for f in features}
    ids = [f["id"] for f in features]

    repo = Path(args.repo) if args.repo else Path(
        run(["git", "rev-parse", "--show-toplevel"], prompts).strip() or prompts)

    policy = load_policy(prompts, args.policy)
    impacts, missing = read_impacts(prompts, ids)

    if missing and not args.force_trunk:
        print("✗ impact prediction missing or failed for:", file=sys.stderr)
        for fid in missing:
            print(f"    {fid}", file=sys.stderr)
        print("\n  Re-run the prediction for those features, or pass --force-trunk to place\n"
              "  them in the trunk without an estimate (recorded in waves.json).", file=sys.stderr)
        return 2

    feature_paths = {fid: {} for fid in ids}
    for fid, impact in impacts.items():
        for p, cat, conf in paths_of(impact):
            feature_paths[fid][p] = {"category": cat, "confidence": conf, "source": "predicted"}

    grep_added = cochange_added = 0
    if not args.no_augment and (repo / ".git").exists():
        grep_added = augment_grep(repo, impacts, feature_paths)
        cochange_added = augment_cochange(repo, feature_paths)

    edges, hubs, owners, completeness_pairs = build_conflict_graph(feature_paths, impacts, policy)

    # Unpredicted features conflict with nothing on paper; keep them off the
    # branch waves entirely so an absent estimate never reads as "no overlap".
    succ, pred = defaultdict(set), defaultdict(set)
    for f in features:
        for dep in f.get("effective_blocked_by", []) or []:
            if dep in meta:
                succ[dep].add(f["id"])
                pred[f["id"]].add(dep)
    # creates -> modifies inference
    creator = {}
    for fid, impact in impacts.items():
        for entry in impact.get("creates", []) or []:
            p = norm(entry.get("path", "") if isinstance(entry, dict) else entry)
            if p:
                creator.setdefault(p, fid)
    for fid, paths in feature_paths.items():
        for p, info in paths.items():
            owner_fid = creator.get(p)
            if owner_fid and owner_fid != fid and info["category"] != "creates":
                succ[owner_fid].add(fid)
                pred[fid].add(owner_fid)

    if missing and args.force_trunk:
        # No estimate is not the same as no overlap. Give an unpredicted feature a
        # strong edge to everything so the repair pass serialises it wherever it
        # legally sits, instead of relocating it and breaking precedence.
        for fid in missing:
            for other in ids:
                if other == fid:
                    continue
                key = tuple(sorted((fid, other)))
                e = edges.setdefault(key, {"grade": ADDITIVE, "files": [], "reasons": []})
                e["grade"] = STRONG
                if "no impact estimate — serialised" not in e["reasons"]:
                    e["reasons"].append("no impact estimate — serialised")

    stages = spine_partition(ids, succ, pred)
    order_index = {f: i for i, f in enumerate(topo_order(ids, succ))}

    before = makespan(stages)
    stages, repair_log = repair(stages, edges, succ, order_index)
    after = makespan(stages)

    # ---- emit
    out_waves, wave_of = [], {}
    counter = 0
    stage_records = []
    for si, st in enumerate(stages):
        kind = "trunk" if len(st) == 1 else "branch"
        names = []
        for wave in st:
            rec = name_wave(wave, "trunk" if kind == "trunk" else "branch", counter, meta)
            rec["stage"] = si
            rec["depends_on"] = [w["name"] for w in out_waves]
            rec["rationale"] = ("serial spine" if kind == "trunk"
                                else "independent chain, no strong file overlap with siblings")
            out_waves.append(rec)
            names.append(rec["name"])
            for f in wave:
                wave_of[f] = rec["name"]
            counter += 1
        stage_records.append({"index": si, "kind": kind, "waves": names})

    # Probe policy: merge-tree is always cheap; build+test only where it earns it.
    # Only a claim split across two waves needs the behavioural probe; inside one
    # wave the extender already runs on the claimant's committed code.
    split_extenders = set()
    for c in completeness_pairs:
        if wave_of.get(c["claimant"]) != wave_of.get(c["extender"]):
            split_extenders.add(c["extender"])
    for si, st in enumerate(stages):
        stage_waves = [w for w in out_waves if w["stage"] == si]
        for wi, rec in enumerate(stage_waves):
            reasons = []
            members = set(rec["features"])
            for (a, b), e in edges.items():
                if e["grade"] != CONDITIONAL:
                    continue
                if (a in members) != (b in members):
                    other = b if a in members else a
                    if wave_of.get(other) and wave_of[other] != rec["name"] \
                       and any(other in w["features"] for w in stage_waves):
                        reasons.append(f"conditional overlap with {wave_of[other]}")
                        break
            if members & split_extenders:
                reasons.append("extends a set another feature claims complete")
            if wi == len(stage_waves) - 1:
                reasons.append("last wave of the stage")
            rec["probe"] = "build-test" if reasons else "merge-tree-only"
            rec["probe_reasons"] = reasons

    doc["schema"] = 3
    doc["status"] = args.status
    doc["stages"] = stage_records
    doc["waves"] = out_waves
    doc["hotspots"] = [
        {"path": h["path"], "touched_by": h["touched_by"], "owner": h.get("owner"),
         "owner_wave": wave_of.get(h.get("owner") or "", None),
         "grade": h["grade"], "rule": h["note"]}
        for h in hubs
    ]
    for f in features:
        f["wave"] = wave_of.get(f["id"])
        f["placement"] = "unpredicted" if f["id"] in missing else "predicted"
        f["impact_ref"] = f".impact/{f['id']}.json"
    if args.status == "final":
        from datetime import datetime, timezone
        doc["finalized_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    graph_doc = {
        "generated_from": str(prompts.name),
        "features": {fid: {p: info for p, info in sorted(paths.items())}
                     for fid, paths in feature_paths.items()},
        "edges": [{"a": a, "b": b, **e} for (a, b), e in sorted(edges.items())],
        "hubs": hubs,
        "additive_owners": owners,
        "completeness_pairs": completeness_pairs,
        "augmentation": {"grep_paths_added": grep_added, "cochange_paths_added": cochange_added},
        "repair_log": repair_log,
        "makespan": {"before_repair": before, "after_repair": after},
    }

    strong_n = sum(1 for e in edges.values() if e["grade"] == STRONG)
    cond_n = sum(1 for e in edges.values() if e["grade"] == CONDITIONAL)
    print(f"features {len(ids)} · predicted {len(impacts)} · unpredicted {len(missing)}")
    print(f"paths: +{grep_added} grep, +{cochange_added} co-change")
    print(f"edges: {strong_n} strong, {cond_n} conditional · hubs {len(hubs)}"
          f" · completeness pairs {len(completeness_pairs)}")
    print(f"stages {len(stage_records)} · waves {len(out_waves)}"
          f" · makespan {before} → {after}")
    for entry in repair_log:
        print(f"  repair: {entry['action']} {entry['features'][0]} / {entry['features'][1]}"
              f" → makespan {entry['makespan']}")
    probes = [w["name"] for w in out_waves if w["probe"] == "build-test"]
    print(f"build+test probe on: {', '.join(probes) if probes else '(none)'}")
    print(f"status: {args.status}")

    if args.dry_run:
        print("\n[dry-run] nothing written")
        return 0

    waves_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (prompts / "conflict-graph.json").write_text(
        json.dumps(graph_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nwrote {waves_path}")
    print(f"wrote {prompts / 'conflict-graph.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
