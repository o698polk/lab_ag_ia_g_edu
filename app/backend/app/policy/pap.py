# Ref: BL-O6-001/002 | Skill: K-020 | Fase: F6
"""PAP — Policy Administration Point (YAML loader)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

from app.core.config import get_settings


@dataclass
class PolicyRule:
    id: str
    effect: str
    actions: list[str]
    roles: list[str]
    permissions: list[str]
    conditions: list[str] = field(default_factory=list)


@dataclass
class PolicyDocument:
    policy_id: str
    version: str
    module: str
    effect_default: str
    description: str
    rules: list[PolicyRule]
    file_path: str


class PAP:
    """Loads and caches versioned YAML policies from policies/v1."""

    def __init__(self, policy_path: Optional[str] = None) -> None:
        settings = get_settings()
        raw = policy_path or settings.policy_path
        path = Path(raw)
        if not path.is_absolute():
            # Resolve relative to repo root (cwd or parents)
            candidates = [
                Path.cwd() / path,
                Path.cwd().parent / path,
                Path(__file__).resolve().parents[4] / path,  # .../lab_ag_ia_g_edu
                Path(__file__).resolve().parents[3] / path,
            ]
            for c in candidates:
                if c.is_dir():
                    path = c
                    break
        self.policy_dir = path
        self._policies: dict[str, PolicyDocument] = {}
        self.load_all()

    def load_all(self) -> list[PolicyDocument]:
        self._policies.clear()
        if not self.policy_dir.is_dir():
            return []
        for yaml_file in sorted(self.policy_dir.glob("*.yaml")):
            data = yaml.safe_load(yaml_file.read_text(encoding="utf-8")) or {}
            rules = [
                PolicyRule(
                    id=str(r.get("id", "")),
                    effect=str(r.get("effect", "DENY")).upper(),
                    actions=[str(a) for a in r.get("actions", [])],
                    roles=[str(x) for x in r.get("roles", [])],
                    permissions=[str(x) for x in r.get("permissions", [])],
                    conditions=[str(c) for c in r.get("conditions", [])],
                )
                for r in data.get("rules", []) or []
            ]
            doc = PolicyDocument(
                policy_id=str(data.get("policy_id", yaml_file.stem)),
                version=str(data.get("version", "v1")),
                module=str(data.get("module", yaml_file.stem)),
                effect_default=str(data.get("effect_default", "DENY")).upper(),
                description=str(data.get("description", "")),
                rules=rules,
                file_path=str(yaml_file),
            )
            self._policies[doc.policy_id] = doc
        return self.list()

    def list(self) -> list[PolicyDocument]:
        return list(self._policies.values())

    def get(self, policy_id: str, version: Optional[str] = None) -> Optional[PolicyDocument]:
        doc = self._policies.get(policy_id)
        if doc is None:
            return None
        if version and doc.version != version:
            return None
        return doc

    def policies_for_action(self, action: str) -> list[PolicyDocument]:
        return [
            p
            for p in self._policies.values()
            if any(action in rule.actions for rule in p.rules)
            or True  # always include all for default-deny evaluation across modules
        ]


_pap: Optional[PAP] = None


def get_pap() -> PAP:
    global _pap
    if _pap is None:
        _pap = PAP()
    return _pap


def reset_pap() -> None:
    global _pap
    _pap = None
