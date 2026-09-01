from __future__ import annotations

import unittest

try:
    from app.api.server import PROJECT_ROOT, _safe_project_path
    from fastapi import HTTPException

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi not installed (only needed for the optional API/UI)")
class SafeProjectPathTests(unittest.TestCase):
    def test_relative_path_inside_project_is_allowed(self):
        resolved = _safe_project_path("inputs/bug_report.md", "bug_report")
        self.assertTrue(str(resolved).startswith(str(PROJECT_ROOT)))

    def test_dotdot_traversal_is_rejected(self):
        with self.assertRaises(HTTPException) as ctx:
            _safe_project_path("../../../../etc/passwd", "logs")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_absolute_path_outside_project_is_rejected(self):
        with self.assertRaises(HTTPException) as ctx:
            _safe_project_path("/etc/passwd", "logs")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_absolute_path_inside_project_is_allowed(self):
        resolved = _safe_project_path(str(PROJECT_ROOT / "mini_repo"), "repo_root")
        self.assertEqual(resolved, PROJECT_ROOT / "mini_repo")


if __name__ == "__main__":
    unittest.main()
