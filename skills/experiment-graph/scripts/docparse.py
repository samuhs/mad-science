"""Parse a pipeline doc into its experiments, stages and stated claims.

Pure and total: never raises on a malformed doc, and never corrects what it reads.
What the doc says is what comes out — judging it is `derive.py`'s job.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# The only status values the doc may use. Anything else is a doc error, flagged
# downstream rather than repaired here.
KNOWN_STATUSES = ("completed", "running", "waiting-to-run", "not-implemented")

_STAGE_RE = re.compile(r"^###\s+Experiment Stage\s+(\d+)\s*(?:[—:-]\s*(.*))?$")
_EXPERIMENT_RE = re.compile(r"^####\s+Experiment\s+(\d+)")
_FIELD_RE = re.compile(r"^\*\*([A-Za-z][A-Za-z ]*?)\*\*:\s*(.*)$")
_ID_RE = re.compile(r"\bE(\d+)\b")
_TITLE_RE = re.compile(r"^#\s+(.*)$")

# Doc claims, extracted only to be cross-checked against the real DAG.
_TABLE_ROW_RE = re.compile(r"^\|\s*(\d+)\s*\|(.*)\|\s*(.*?)\s*\|\s*$")
# Accepts the English label and the Portuguese one ("Caminho crítico").
_CRIT_CLAIM_RE = re.compile(
    r"^\*\*(?:Critical path|Caminho cr[íi]tico):\*\*\s*(.+)$", re.IGNORECASE
)


@dataclass
class Experiment:
    """One `#### Experiment N` block, exactly as written in the doc."""

    num: int
    title: str = ""
    goals: str = ""
    status: str = ""
    blocked_by: list[str] = field(default_factory=list)
    result: str = ""
    stage: int = 1
    human: bool | None = None

    @property
    def id(self) -> str:
        return f"E{self.num}"


@dataclass
class DocClaims:
    """What the doc's own summary asserts. Claims to check, never facts to trust."""

    layers: dict[int, list[str]] = field(default_factory=dict)
    critical_path: list[str] = field(default_factory=list)


def _clean(value: str) -> str:
    """Strip markdown emphasis/backticks; treat the empty marker as empty."""
    text = value.strip().replace("**", "").replace("`", "").strip()
    return "" if text in {"—", "-", "--"} else text


def _read_lines(path: str) -> list[str]:
    with open(path, encoding="utf-8") as handle:
        return handle.read().splitlines()


def _title_of(lines: list[str]) -> str:
    for line in lines:
        heading = _TITLE_RE.match(line)
        if heading:
            return _clean(heading.group(1).split("—", 1)[-1])
    return ""


def _stages_of(lines: list[str]) -> list[dict]:
    stages = []
    for line in lines:
        match = _STAGE_RE.match(line)
        if match:
            stages.append({"n": int(match.group(1)), "name": _clean(match.group(2) or "")})
    return stages


def _blocks_of(lines: list[str]) -> list[tuple[int, int, list[str]]]:
    """Slice the doc into `(experiment number, stage number, block lines)`."""
    blocks: list[tuple[int, int, list[str]]] = []
    stage, num, current = 1, None, []
    for line in lines:
        stage_match = _STAGE_RE.match(line)
        if stage_match:
            if num is not None:
                blocks.append((num, stage, current))
                num, current = None, []
            stage = int(stage_match.group(1))
            continue
        match = _EXPERIMENT_RE.match(line)
        if match:
            if num is not None:
                blocks.append((num, stage, current))
            num, current = int(match.group(1)), []
            continue
        if num is None:
            continue
        if line.startswith("###"):  # any other heading ends the block
            blocks.append((num, stage, current))
            num, current = None, []
        else:
            current.append(line)
    if num is not None:
        blocks.append((num, stage, current))
    return blocks


def _collect_fields(lines: list[str]) -> dict[str, str]:
    """Fold `**Field**: value` lines, including their continuation lines."""
    fields: dict[str, str] = {}
    current: str | None = None
    for line in lines:
        match = _FIELD_RE.match(line)
        if match:
            key = match.group(1).strip().lower()
            current = key
            fields[key] = match.group(2).strip()
        elif current and line.strip():
            fields[current] = f"{fields[current]} {line.strip()}".strip()
    return fields


def _experiment_of(num: int, stage: int, block: list[str]) -> Experiment:
    fields = _collect_fields(block)
    blocked = _clean(fields.get("blocked by", ""))
    experiment = Experiment(
        num=num,
        stage=stage,
        title=_clean(fields.get("title", "")),
        goals=_clean(fields.get("goals", "")),
        status=_clean(fields.get("status", "")).lower(),
        result=_clean(fields.get("result", "")),
        blocked_by=sorted({f"E{m}" for m in _ID_RE.findall(blocked)}, key=lambda i: int(i[1:])),
    )
    if "human" in fields:
        experiment.human = _clean(fields["human"]).lower() in {"true", "yes", "sim"}
    return experiment


def _parse_claims(lines: list[str], claims: DocClaims) -> None:
    """Extract the doc's stated layers and critical path, for cross-checking."""
    for line in lines:
        claim = _CRIT_CLAIM_RE.match(line)
        if claim:
            claims.critical_path = [f"E{m}" for m in _ID_RE.findall(claim.group(1))]
            continue
        row = _TABLE_ROW_RE.match(line)
        if not row:
            continue
        ids = [f"E{m}" for m in _ID_RE.findall(row.group(2))]
        if ids:
            claims.layers.setdefault(int(row.group(1)), []).extend(ids)


def parse(path: str) -> tuple[str, list[dict], list[Experiment], DocClaims]:
    """Read a pipeline doc into its title, stages, experiments and claims."""
    lines = _read_lines(path)
    claims = DocClaims()
    _parse_claims(lines, claims)
    experiments = [_experiment_of(n, s, b) for n, s, b in _blocks_of(lines)]
    return _title_of(lines), _stages_of(lines), experiments, claims