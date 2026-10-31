"""Exercise the structure checker against real, temporary source trees."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CHECKER = Path(__file__).resolve().parents[1] / "check_structure.py"


class StructureCheckerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "repo"
        self.root.mkdir()

    def source(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def run_checker(self, *paths):
        result = subprocess.run(
            [sys.executable, "-B", str(CHECKER), "--repo-root", str(self.root),
             *(str(path) for path in paths)],
            capture_output=True, text=True, check=False,
        )
        self.assertIn(result.returncode, (0, 1, 2), result.stderr)
        self.assertEqual(result.stderr, "")
        findings = json.loads(result.stdout)
        for finding in findings:
            self.assertEqual(set(finding), {"file", "line", "code", "message"})
            self.assertIsInstance(finding["line"], int)
        return result.returncode, findings

    def codes(self, findings):
        return [finding["code"] for finding in findings]

    def symlink(self, target, link, directory=False):
        try:
            link.symlink_to(target, target_is_directory=directory)
        except (OSError, NotImplementedError) as error:
            self.skipTest("Symlinks unavailable: {}".format(error))

    def test_explicit_direct_imports_are_valid_and_other_files_are_not_scanned(self):
        self.source("service.py", "from project.models.user import User\n")
        self.source("unselected.py", "from project import *\n")
        self.assertEqual(self.run_checker("service.py"), (0, []))

    def test_requires_explicit_targets(self):
        status, findings = self.run_checker()
        self.assertEqual(status, 2)
        self.assertEqual(self.codes(findings), ["INPUT_ERROR"])

    def test_nested_wildcard_import_is_reported_with_exact_line(self):
        self.source("module.py", "if enabled:\n    from project import *\n")
        status, findings = self.run_checker("module.py")
        self.assertEqual(status, 1)
        self.assertEqual(self.codes(findings), ["STRUCT001"])
        self.assertEqual((findings[0]["file"], findings[0]["line"]), ("module.py", 2))

    def test_strings_containing_rule_examples_are_not_code(self):
        self.source("guide.py", '"""from project import *\nclass User(BaseModel): pass"""\n')
        self.assertEqual(self.run_checker("guide.py"), (0, []))

    def test_init_allows_only_one_module_docstring_and_comments(self):
        self.source("pkg/__init__.py", '"""Package description."""\n# No execution.\n')
        self.assertEqual(self.run_checker("pkg"), (0, []))

    def test_init_rejects_imports_exports_and_other_statements(self):
        self.source("pkg/__init__.py", '"""Package."""\nfrom .user import User\n__all__ = ["User"]\npass\n')
        status, findings = self.run_checker("pkg")
        self.assertEqual(status, 1)
        self.assertEqual(self.codes(findings), ["STRUCT002"] * 3)
        self.assertEqual([item["line"] for item in findings], [2, 3, 4])

    def test_recognizes_aliased_dataclass_decorators(self):
        self.source("service.py", "from dataclasses import dataclass as record\n@record(frozen=True)\nclass Config:\n    value: int\n")
        status, findings = self.run_checker("service.py")
        self.assertEqual(status, 1)
        self.assertEqual(self.codes(findings), ["STRUCT003"])
        self.assertEqual(findings[0]["line"], 3)

    def test_recognizes_module_aliases_and_imported_model_bases(self):
        cases = (
            ("import dataclasses as dc\n@dc.dataclass\nclass Config: pass\n", 3),
            ("import pydantic as pd\nclass User(pd.BaseModel): pass\n", 2),
            ("from pydantic.v1 import BaseModel as Base\nclass User(Base): pass\n", 2),
            ("from pydantic_settings import BaseSettings as Settings\nclass Config(Settings): pass\n", 2),
            ("from enum import IntEnum as Choice\nclass Color(Choice): RED = 1\n", 2),
            ("from typing import NamedTuple as Tuple\nclass Point(Tuple): x: int\n", 2),
            ("from typing_extensions import TypedDict as Record\nclass Row(Record): x: int\n", 2),
            ("from pydantic.dataclasses import dataclass as record\n@record\nclass Row: x: int\n", 3),
        )
        for source, line in cases:
            with self.subTest(source=source):
                self.source("service.py", source)
                status, findings = self.run_checker("service.py")
                self.assertEqual(status, 1)
                self.assertEqual(self.codes(findings), ["STRUCT003"])
                self.assertEqual(findings[0]["line"], line)

    def test_recognizes_model_factories_and_local_inheritance(self):
        self.source("service.py", "from typing import NamedTuple\nPoint = NamedTuple('Point', [('x', int)])\nclass SpecialPoint(Point): pass\n")
        status, findings = self.run_checker("service.py")
        self.assertEqual(status, 1)
        self.assertEqual(self.codes(findings), ["STRUCT003", "STRUCT003"])
        self.assertEqual([item["line"] for item in findings], [2, 3])

    def test_allows_models_in_any_actual_models_directory(self):
        self.source("feature/models/config.py", "from dataclasses import dataclass\n@dataclass\nclass Config: pass\n")
        self.assertEqual(self.run_checker("feature"), (0, []))

    def test_models_py_filename_is_not_a_models_directory(self):
        self.source("models.py", "from enum import Enum\nclass Mode(Enum): A = 1\n")
        status, findings = self.run_checker("models.py")
        self.assertEqual(status, 1)
        self.assertEqual(self.codes(findings), ["STRUCT003"])

    def test_ignores_plain_service_names_and_unrelated_decorators(self):
        self.source("service.py", "from project.decorators import dataclass\nclass UserModel: pass\n@dataclass\nclass DataService: pass\nclass Plain(BaseModel): pass\n")
        self.assertEqual(self.run_checker("service.py"), (0, []))

    def test_reassigned_import_and_argument_shadows_are_not_model_evidence(self):
        self.source("service.py", "from dataclasses import dataclass\ndataclass = custom\n@dataclass\nclass Service: pass\nimport pydantic as pd\ndef build(pd):\n    class Service(pd.BaseModel): pass\n")
        self.assertEqual(self.run_checker("service.py"), (0, []))

    def test_local_import_model_alias_does_not_leak_out_of_function(self):
        self.source("service.py", "def build():\n    from enum import Enum as E\n    class Mode(E): A = 1\nclass Service(E): pass\n")
        status, findings = self.run_checker("service.py")
        self.assertEqual(status, 1)
        self.assertEqual(self.codes(findings), ["STRUCT003"])
        self.assertEqual(findings[0]["line"], 3)

    def test_test_models_are_exempt_but_import_and_init_rules_still_apply(self):
        self.source("tests/fixtures.py", "from dataclasses import dataclass\n@dataclass\nclass Fixture: pass\nfrom project import *\n")
        self.source("feature/test_helpers.py", "from enum import Enum\nclass Choice(Enum): A = 1\n")
        self.source("tests/__init__.py", "__all__ = []\n")
        status, findings = self.run_checker("tests", "feature")
        self.assertEqual(status, 1)
        self.assertEqual(set(self.codes(findings)), {"STRUCT001", "STRUCT002"})

    def test_dependency_calls_in_router_and_app_are_reported(self):
        self.source("app.py", "from project.services import OrderService as Service\nfrom sqlalchemy.orm import sessionmaker as sessions\nservice = Service()\nfactory = sessions()\n")
        self.source("routers/orders.py", "import project.repositories as repos\ndef get_order():\n    return repos.OrderRepository()\n")
        status, findings = self.run_checker("app.py", "routers")
        self.assertEqual(status, 1)
        self.assertEqual(self.codes(findings), ["STRUCT004"] * 3)

    def test_dependency_factory_aliases_are_resolved(self):
        self.source("main.py", "import sqlalchemy.ext.asyncio as db\nengine = db.create_async_engine('url')\nsessions = db.async_sessionmaker(engine)\n")
        status, findings = self.run_checker("main.py")
        self.assertEqual(status, 1)
        self.assertEqual(self.codes(findings), ["STRUCT004", "STRUCT004"])

    def test_dependency_calls_are_allowed_in_dependency_concern_modules(self):
        text = "from project.services import OrderService\nservice = OrderService()\n"
        self.source("dependencies/orders.py", text)
        self.source("dependencies/main.py", text)
        self.source("services/orders.py", text)
        self.assertEqual(self.run_checker("dependencies", "services"), (0, []))

    def test_dependency_session_constructor_aliases_are_reported(self):
        self.source("app.py", "from sqlalchemy.orm import Session as S\nfrom sqlalchemy.ext.asyncio import AsyncSession as A\nimport sqlalchemy.orm as orm\nfirst = S()\nsecond = A()\nthird = orm.Session()\n")
        status, findings = self.run_checker("app.py")
        self.assertEqual(status, 1)
        self.assertEqual(self.codes(findings), ["STRUCT004"] * 3)

    def test_recognizes_pydantic_root_model_with_alias_and_generic_base(self):
        self.source("service.py", "from pydantic import RootModel as Root\nclass Values(Root[list[str]]): pass\n")
        status, findings = self.run_checker("service.py")
        self.assertEqual(status, 1)
        self.assertEqual(self.codes(findings), ["STRUCT003"])

    def test_conventional_tests_module_allows_fixture_models_but_not_wildcards(self):
        self.source("tests.py", "from dataclasses import dataclass\n@dataclass\nclass Fixture:\n    value: int\nfrom project import *\n")
        status, findings = self.run_checker("tests.py")
        self.assertEqual(status, 1)
        self.assertEqual(self.codes(findings), ["STRUCT001"])

    def test_dependency_checks_do_not_guess_get_functions_or_plain_capitalized_names(self):
        self.source("router.py", "from project import get_service, User\nfrom project import create_engine\nx = get_service()\ny = User()\nz = create_engine()\n")
        self.assertEqual(self.run_checker("router.py"), (0, []))

    def test_loop_context_and_exception_targets_shadow_imported_model_names(self):
        self.source("service.py", "from enum import Enum\nfor Enum in bases:\n    class Service(Enum): pass\nfrom pydantic import BaseModel\nwith manager as BaseModel:\n    class Service(BaseModel): pass\nfrom typing import NamedTuple\ntry:\n    run()\nexcept Error as NamedTuple:\n    class Service(NamedTuple): pass\n")
        self.assertEqual(self.run_checker("service.py"), (0, []))

    def test_lambda_and_comprehension_targets_shadow_imported_constructors(self):
        self.source("router.py", "from project import HttpClient\nf = lambda HttpClient: HttpClient()\na = [HttpClient() for HttpClient in factories]\nb = {HttpClient() for HttpClient in factories}\nc = {HttpClient(): 1 for HttpClient in factories}\nd = (HttpClient() for HttpClient in factories)\n")
        self.assertEqual(self.run_checker("router.py"), (0, []))

    def test_comprehension_scope_does_not_hide_later_constructor_use(self):
        self.source("router.py", "from project import HttpClient\na = [HttpClient for HttpClient in factories]\nclient = HttpClient()\n")
        status, findings = self.run_checker("router.py")
        self.assertEqual(status, 1)
        self.assertEqual(self.codes(findings), ["STRUCT004"])
        self.assertEqual(findings[0]["line"], 3)

    def test_directory_targets_deduplicate_files_and_ignore_non_python_files(self):
        self.source("pkg/module.py", "from project import *\n")
        self.source("pkg/readme.txt", "from project import *\n")
        status, findings = self.run_checker("pkg", "pkg/module.py", "pkg")
        self.assertEqual(status, 1)
        self.assertEqual(len(findings), 1)

    def test_missing_non_python_and_outside_paths_are_input_errors(self):
        self.source("notes.txt", "text")
        outside = Path(self.temporary.name) / "outside.py"
        outside.write_text("from secret import *\n", encoding="utf-8")
        status, findings = self.run_checker("missing.py", "notes.txt", outside)
        self.assertEqual(status, 2)
        self.assertEqual(set(self.codes(findings)), {"INPUT_ERROR", "OUTSIDE_ROOT"})
        self.assertEqual(len(findings), 3)

    def test_missing_repo_root_is_an_input_error(self):
        self.root.rmdir()
        status, findings = self.run_checker("module.py")
        self.assertEqual(status, 2)
        self.assertEqual(self.codes(findings), ["INPUT_ERROR"])

    def test_syntax_and_decode_failures_are_errors_and_do_not_hide_violations(self):
        self.source("broken.py", "def broken(:\n")
        self.source("good.py", "from project import *\n")
        (self.root / "invalid.py").write_bytes(b"\xff")
        status, findings = self.run_checker(".")
        self.assertEqual(status, 2)
        self.assertEqual(set(self.codes(findings)), {"SYNTAX_ERROR", "READ_ERROR", "STRUCT001"})

    def test_python_encoding_cookie_is_respected(self):
        (self.root / "encoded.py").write_bytes(b"# coding: latin-1\nname = 'caf\xe9'\n")
        self.assertEqual(self.run_checker("encoded.py"), (0, []))

    def test_ast_depth_limit_is_an_error_instead_of_a_crash(self):
        self.source("deep.py", "value = " + " + ".join(["1"] * 1200))
        status, findings = self.run_checker("deep.py")
        self.assertEqual(status, 2)
        self.assertEqual(self.codes(findings), ["CHECK_ERROR"])

    @unittest.skipIf(os.name == "nt", "POSIX permissions test")
    def test_unreadable_source_is_an_error(self):
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            self.skipTest("Root can read files without permission bits")
        path = self.source("unreadable.py", "pass\n")
        path.chmod(0)
        self.addCleanup(path.chmod, 0o600)
        status, findings = self.run_checker("unreadable.py")
        self.assertEqual(status, 2)
        self.assertEqual(self.codes(findings), ["READ_ERROR"])

    def test_file_symlink_escape_is_rejected(self):
        outside = Path(self.temporary.name) / "outside.py"
        outside.write_text("from secret import *\n", encoding="utf-8")
        self.symlink(outside, self.root / "escape.py")
        status, findings = self.run_checker("escape.py")
        self.assertEqual(status, 2)
        self.assertEqual(self.codes(findings), ["OUTSIDE_ROOT"])

    def test_internal_file_symlink_uses_real_source_ownership(self):
        target = self.source("service.py", "from enum import Enum\nclass Mode(Enum): A = 1\n")
        (self.root / "models").mkdir()
        self.symlink(target, self.root / "models/alias.py")
        status, findings = self.run_checker("models/alias.py")
        self.assertEqual(status, 1)
        self.assertEqual(self.codes(findings), ["STRUCT003"])
        self.assertEqual(findings[0]["file"], "service.py")

    def test_internal_init_file_symlink_cannot_hide_initializer_code(self):
        target = self.source("package/__init__.py", "from .models import User\n")
        self.symlink(target, self.root / "friendly.py")
        status, findings = self.run_checker("friendly.py")
        self.assertEqual(status, 1)
        self.assertEqual(self.codes(findings), ["STRUCT002"])
        self.assertEqual(findings[0]["file"], "package/__init__.py")

    def test_directory_symlinks_are_reported_without_being_traversed(self):
        self.source("real/module.py", "from project import *\n")
        self.symlink(self.root / "real", self.root / "link", directory=True)
        status, findings = self.run_checker(".")
        self.assertEqual(status, 2)
        self.assertEqual(set(self.codes(findings)), {"INPUT_ERROR", "STRUCT001"})
        self.assertEqual(len(findings), 2)

    def test_explicit_path_through_directory_symlink_is_rejected(self):
        self.source("real/module.py", "from project import *\n")
        self.symlink(self.root / "real", self.root / "link", directory=True)
        status, findings = self.run_checker("link/module.py")
        self.assertEqual(status, 2)
        self.assertEqual(self.codes(findings), ["INPUT_ERROR"])


if __name__ == "__main__":
    unittest.main()
