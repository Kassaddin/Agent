"""GET-only provider fixtures, bounded downloads, and redirect credential handling."""
import io
import json
from pathlib import Path
import sys
import unittest
from unittest import mock
from urllib.error import HTTPError
from urllib.request import Request

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import release_source as net
import release_format as fmt
from test_update import artifact, payload


class Response(io.BytesIO):
    pass


class Opener:
    def __init__(self, values):
        self.values = values
        self.calls = []

    def open(self, request, timeout):
        self.calls.append((request, timeout))
        value = self.values[request.full_url]
        if isinstance(value, Exception):
            raise value
        return Response(value if isinstance(value, bytes) else json.dumps(value).encode())


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.base = "https://api.github.com/repos/example/kit"
        raw, checksum = artifact(payload())
        self.release = {"id": 1, "tag_name": "v1.0.0", "draft": False, "prerelease": False, "published_at": "2026-11-23T00:00:00Z",
                        "assets": [{"id": 10, "name": "agent-skills.zip", "state": "uploaded", "url": self.base + "/releases/assets/10", "digest": "sha256:" + fmt.sha(raw)},
                                   {"id": 11, "name": "agent-skills.zip.sha256", "state": "uploaded", "url": self.base + "/releases/assets/11"}]}
        self.values = {self.base + "/releases/latest": self.release, self.base + "/releases/tags/v1.0.0": self.release,
                       self.base + "/releases/assets/10": raw, self.base + "/releases/assets/11": checksum}

    def test_reads_only_published_metadata_and_asset_gets(self):
        opener = Opener(self.values)
        source = net.GitHubSource("example/kit", opener=opener)
        package = source.package(source.select())
        self.assertEqual(package["manifest"]["version"], "v1.0.0")
        self.assertEqual(len(opener.calls), 3)
        self.assertTrue(all(request.get_method() == "GET" and timeout <= 20 for request, timeout in opener.calls))

    def test_authorization_is_rechecked_before_each_request(self):
        opener = Opener(self.values)
        gate = mock.Mock(side_effect=[None, net.SourceError("Policy changed")])
        source = net.GitHubSource("example/kit", opener=opener, authorize=gate)
        selected = source.select()
        with self.assertRaises(net.SourceError):
            source.package(selected)
        self.assertEqual(len(opener.calls), 1)

    def test_empty_published_list_distinguishes_no_release_from_inaccessibility(self):
        values = {self.base + "/releases/latest": HTTPError(self.base, 404, "missing", {}, None), self.base + "/releases?per_page=5": []}
        with self.assertRaises(net.NoRelease):
            net.GitHubSource("example/kit", opener=Opener(values)).select()
        values[self.base + "/releases?per_page=5"] = HTTPError(self.base, 404, "hidden", {}, None)
        with self.assertRaises(net.SourceError) as raised:
            net.GitHubSource("example/kit", opener=Opener(values)).select()
        self.assertNotIsInstance(raised.exception, net.NoRelease)

    def test_wrong_asset_repository_or_api_digest_is_rejected(self):
        self.release["assets"][0]["url"] = "https://api.github.com/repos/other/kit/releases/assets/10"
        source = net.GitHubSource("example/kit", opener=Opener(self.values))
        with self.assertRaises(net.SourceError):
            source.package(source.select())
        self.release["assets"][0]["url"] = self.base + "/releases/assets/10"
        self.release["assets"][0]["digest"] = "sha256:" + "0" * 64
        with self.assertRaises(fmt.ReleaseError):
            source.package(source.select())

    def test_redirects_are_provider_bound_and_strip_cross_host_auth(self):
        handler = net.ProviderRedirects()
        request = Request(self.base + "/releases/assets/10", headers={"Authorization": "Bearer fixture-secret"})
        redirected = handler.redirect_request(request, None, 302, "", {}, "https://release-assets.githubusercontent.com/signed?value=fixture")
        self.assertIsNone(redirected.get_header("Authorization"))
        with self.assertRaises(net.SourceError):
            handler.redirect_request(request, None, 302, "", {}, "https://unlisted.example/file.zip")
        with self.assertRaises(net.SourceError):
            handler.redirect_request(request, None, 302, "", {}, "http://github.com/file.zip")

    def test_expired_budget_and_response_size_are_explicit(self):
        opener = Opener(self.values)
        source = net.GitHubSource("example/kit", opener=opener)
        source.deadline = 0
        with self.assertRaises(net.SourceError):
            source.select()
        self.assertEqual(opener.calls, [])
        source = net.GitHubSource("example/kit", opener=opener)
        with self.assertRaises(net.SourceError):
            source.get(self.base + "/releases/assets/10", 10, binary=True)

    def test_draft_or_unrequested_prerelease_is_not_selected(self):
        source = net.GitHubSource("example/kit", opener=Opener(self.values))
        self.release["prerelease"] = True
        with self.assertRaises(net.SourceError):
            source.select()
        self.assertEqual(source.select("v1.0.0")["tag_name"], "v1.0.0")
        self.release["draft"] = True
        with self.assertRaises(net.SourceError):
            source.select("v1.0.0")

    def test_repository_identity_does_not_accept_unlisted_provider_urls(self):
        self.assertEqual(net.repository_identity("https://github.com/example/kit.git"), "example/kit")
        for value in ("http://github.com/example/kit", "https://elsewhere.example/example/kit", "https://github.com/example/kit?token=bad", "https://github.com/example/kit/tree/main"):
            with self.assertRaises(net.SourceError):
                net.repository_identity(value)


if __name__ == "__main__":
    unittest.main()
