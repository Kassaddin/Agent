"""Bounded GET-only GitHub release access; never invokes Git or publishes anything."""
from __future__ import annotations
import json
import os
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from release_format import MAX_ARCHIVE, ReleaseError, strict_json, unpack


class SourceError(RuntimeError):
    pass


class NoRelease(SourceError):
    pass


def repository_identity(url):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != "github.com" or parsed.query or parsed.fragment or parsed.username:
        raise SourceError("MVP release sources require the configured HTTPS GitHub repository identity")
    match = re.fullmatch(r"/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?", parsed.path)
    if not match or match[1] in {".", ".."} or match[2] in {".", ".."}:
        raise SourceError("Invalid repository identity")
    return f"{match[1]}/{match[2]}"


class ProviderRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        parsed = urlsplit(newurl)
        if parsed.scheme != "https" or parsed.hostname not in {"api.github.com", "github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com"} or parsed.username or parsed.port not in {None, 443}:
            raise SourceError("Release download redirected outside the approved provider")
        redirected = super().redirect_request(request, fp, code, message, headers, newurl)
        if redirected and urlsplit(request.full_url).hostname != parsed.hostname:
            redirected.remove_header("Authorization")
        return redirected


class GitHubSource:
    def __init__(self, repository, *, opener=None, timeout=20, budget=120, authorize=None):
        self.repository = repository
        self.base = "https://api.github.com/repos/" + repository
        self.opener = opener or build_opener(ProviderRedirects())
        self.timeout = timeout
        self.deadline = time.monotonic() + budget
        self.authorize = authorize

    def get(self, url, limit, *, binary=False):
        if self.authorize:
            self.authorize()
        if not url.startswith(self.base + "/releases"):
            raise SourceError("Request is outside the selected repository's release endpoints")
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise SourceError("Release request budget exhausted")
        headers = {"Accept": "application/octet-stream" if binary else "application/vnd.github+json",
                   "User-Agent": "agent-skills-update", "X-GitHub-Api-Version": "2026-03-10"}
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = "Bearer " + token
        try:
            with self.opener.open(Request(url, headers=headers, method="GET"), timeout=min(self.timeout, remaining)) as response:
                chunks, length = [], 0
                reader = getattr(response, "read1", response.read)
                while length <= limit:
                    if time.monotonic() >= self.deadline:
                        raise SourceError("Release request budget exhausted")
                    chunk = reader(min(65536, limit + 1 - length))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    length += len(chunk)
                raw = b"".join(chunks)
            if len(raw) > limit:
                raise SourceError("Release response exceeds the download limit")
            return raw if binary else strict_json(raw)
        except HTTPError as exc:
            exc.close()
            raise
        except (URLError, OSError, ValueError) as exc:
            raise SourceError("Release request failed; recheck source access or connection") from exc

    def releases(self):
        data = self.get(self.base + "/releases?per_page=5", 2 * 1024 * 1024)
        if not isinstance(data, list):
            raise SourceError("Provider returned an invalid release list")
        return [item for item in data if isinstance(item, dict) and item.get("draft") is False and item.get("published_at")]

    def select(self, version=None):
        url = self.base + ("/releases/tags/" + quote(version, safe="") if version else "/releases/latest")
        try:
            data = self.get(url, 2 * 1024 * 1024)
        except HTTPError as exc:
            if exc.code == 404 and version is None:
                try:
                    visible = self.releases()
                except HTTPError as hidden:
                    raise SourceError("Repository release access is unavailable; no absence was established") from hidden
                if not any(not item.get("prerelease") for item in visible):
                    raise NoRelease("No published stable release is available") from exc
            raise SourceError("Requested published release could not be read") from exc
        if not isinstance(data, dict) or data.get("draft") is not False or not data.get("published_at") or (not version and data.get("prerelease")):
            raise SourceError("A published release was not established")
        if version and data.get("tag_name") != version:
            raise SourceError("Provider release tag differs from the requested version")
        if type(data.get("id")) is not int or data["id"] < 1 or not isinstance(data.get("tag_name"), str):
            raise SourceError("Release identity is invalid")
        return data

    def package(self, release, *, legacy_baseline=False):
        assets = release.get("assets")
        if not isinstance(assets, list):
            raise SourceError("Release assets are unavailable")
        selected = {}
        for name in ("agent-skills.zip", "agent-skills.zip.sha256"):
            matches = [item for item in assets if isinstance(item, dict) and item.get("name") == name and item.get("state") == "uploaded"]
            if len(matches) != 1 or type(matches[0].get("id")) is not int or matches[0]["id"] < 1:
                raise SourceError("Release needs exactly one uploaded ZIP and checksum asset")
            item = matches[0]
            expected = self.base + "/releases/assets/" + str(item["id"])
            if item.get("url") != expected:
                raise SourceError("Asset identity is outside the selected repository")
            selected[name] = item
        raw = self.get(selected["agent-skills.zip"]["url"], MAX_ARCHIVE, binary=True)
        checksum = self.get(selected["agent-skills.zip.sha256"]["url"], 1024, binary=True)
        data = unpack(raw, checksum, release["tag_name"], legacy_baseline=legacy_baseline)
        api_digest = selected["agent-skills.zip"].get("digest")
        if api_digest is not None and api_digest != "sha256:" + data["archive_sha256"]:
            raise ReleaseError("Provider asset digest differs from the downloaded ZIP")
        data["identity"] = {"repository": self.repository, "version": release["tag_name"], "release_id": release["id"],
                            "asset_id": selected["agent-skills.zip"]["id"], "archive_sha256": data["archive_sha256"]}
        return data
