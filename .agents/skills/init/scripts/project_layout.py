#!/usr/bin/env python3
"""Read-only project path selection. Locations never grant access or activate policy."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def absolute(path):
    return Path(os.path.abspath(path))


def discover_boundaries(project_root, explicit=None):
    root = absolute(project_root)
    if explicit is not None:
        path = Path(explicit)
        return absolute(path if path.is_absolute() else root / path)
    candidates = [root / name for name in ('.agents/config/BOUNDARIES.yaml', 'Agents/.agents/config/BOUNDARIES.yaml', '.agent/config/BOUNDARIES.yaml', 'Agents/.agent/config/BOUNDARIES.yaml', 'BOUNDARIES.yaml')]
    def present(path):
        try:
            path.stat()
            return True
        except FileNotFoundError:
            return False
    found = [path for path in candidates if present(path)]
    if len(found) > 1:
        raise ValueError("Multiple boundary files exist; select the authoritative file explicitly")
    if found:
        return found[0]
    areas = [path for path in candidates[:2] if path.parent.parent.is_dir()]
    if len(areas) > 1:
        raise ValueError("Multiple agent areas exist; select the intended missing policy location explicitly")
    return areas[0] if areas else candidates[0]


class ProjectLayout:
    def __init__(self, project_root, boundaries, agent_home=None):
        self.root = absolute(project_root)
        self.boundaries = absolute(boundaries)
        if agent_home is not None:
            selected = Path(agent_home)
            self.home = absolute(selected if selected.is_absolute() else self.root / selected)
        elif self.boundaries.name == "BOUNDARIES.yaml" and self.boundaries.parent.name == "config" and self.boundaries.parent.parent.name in {'.agent', '.agents'}:
            self.home = self.boundaries.parent.parent
        else:
            self.home = self.root / ".agents"
        if self.home == self.root or not self.home.is_relative_to(self.root) or not self.home.resolve().is_relative_to(self.root.resolve()):
            raise ValueError("The selected agent area must stay within the primary project")
        self.legacy = agent_home is None and not (self.boundaries.name == "BOUNDARIES.yaml" and self.boundaries.parent.name == "config" and self.boundaries.parent.parent.name in {'.agent', '.agents'})
        self.human = self.home.parent / "docs"
        self.context = self.home / "context"
        self.index = self.root / "context/index.yaml" if self.legacy else self.context / "index.yaml"
        self.view = self.root / "CONTEXT.md" if self.legacy else self.context / "project.md"
        self.areas = self.root / "context/areas" if self.legacy else self.context / "areas"
        self.checkpoints = self.home / "state/checkpoints"
        self.reports = self.home / "reports"

    def relative(self, path):
        return absolute(path).relative_to(self.root).as_posix()

    def is_context_artifact(self, path):
        candidate = absolute(path).resolve()
        return candidate == self.index.resolve() or candidate == self.view.resolve() or candidate.is_relative_to(self.areas.resolve())

    def reader_report_directory(self, directory):
        relative = absolute(directory).relative_to(self.reports)
        return self.human / "reports" / relative


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--boundaries", type=Path)
    parser.add_argument("--agent-home", type=Path)
    args = parser.parse_args(argv)
    try:
        boundary = discover_boundaries(args.project_root, args.boundaries)
        layout = ProjectLayout(args.project_root, boundary, args.agent_home)
        print(json.dumps({"read_only": True, "boundaries": str(boundary), "boundary_present": boundary.is_file(),
                          "agent_home": str(layout.home), "context_index": str(layout.index), "context_view": str(layout.view),
                          "checkpoints": str(layout.checkpoints), "structured_reports": str(layout.reports),
                          "fallback_human_documents": str(layout.human), "legacy": layout.legacy,
                          "note": "Use established host document locations before this fallback; validate current permissions before access."}))
        return 0
    except (OSError, ValueError):
        print(json.dumps({"status": "error", "read_only": True, "reason": "Select one boundary file and an agent area within the primary project"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
