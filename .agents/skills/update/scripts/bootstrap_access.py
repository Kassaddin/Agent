"""Shared scoped bootstrap access. Packaged by Setup; maintained by Update."""
from pathlib import Path
import os
import update_kit as shared

def absolute(path):
    return Path(os.path.abspath(path))

def no_links(path):
    for part in (path, *path.parents):
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise shared.Blocked('Kit operations do not follow links or junctions')

def boundary_candidates(root):
    return [root / name for name in ('.agents/config/BOUNDARIES.yaml', 'Agents/.agents/config/BOUNDARIES.yaml', '.agent/config/BOUNDARIES.yaml', 'Agents/.agent/config/BOUNDARIES.yaml', 'BOUNDARIES.yaml')]

def discover(root, explicit=None):
    if explicit is not None:
        selected = absolute(explicit if Path(explicit).is_absolute() else root / explicit)
        no_links(selected)
        if not selected.is_file():
            raise shared.Blocked('The explicitly selected boundary file is unavailable')
        return selected
    found = []
    for path in boundary_candidates(root):
        no_links(path)
        if path.exists():
            found.append(path)
    if len(found) > 1:
        raise shared.Blocked('Multiple boundary files exist; select one explicitly')
    return found[0] if found else None

class BootstrapAccess:
    """Only an explicitly approved source/kit operation; never a saved policy."""
    def __init__(self, root):
        self.root = absolute(root)
        self.kit = self.root / 'Agents'

    def require(self, path, op='read'):
        path = absolute(path)
        no_links(path)
        if discover(self.root) is not None:
            raise shared.Blocked('Boundaries appeared; reload before further bootstrap operations')
        if path == self.root and op == 'read':
            return
        if not path.is_relative_to(self.kit) or op not in {'read', 'create', 'modify', 'delete'}:
            raise shared.Blocked('Bootstrap approval covers only the stated project kit')

    def read(self, path):
        self.require(path)
        if not path.exists():
            return None
        if not path.is_file() or path.stat().st_size > 8 * 1024 * 1024:
            raise shared.Blocked('Expected a bounded regular bootstrap file')
        return path.read_bytes()
