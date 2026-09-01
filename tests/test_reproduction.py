from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.agents import reproduction


class EstimateArityTests(unittest.TestCase):
    def test_no_params(self):
        source = "def ping():\n    return True\n"
        self.assertEqual(reproduction._estimate_arity("ping", source), 0)

    def test_single_param(self):
        source = "def average(nums: list[float]) -> float:\n    return sum(nums) / len(nums)\n"
        self.assertEqual(reproduction._estimate_arity("average", source), 1)

    def test_two_params(self):
        source = "def get_line_item_price(catalog: dict[str, float], sku: str) -> float:\n    return catalog[sku]\n"
        self.assertEqual(reproduction._estimate_arity("get_line_item_price", source), 2)

    def test_nested_brackets_dont_confuse_the_comma_count(self):
        source = "def f(catalog: dict[str, float], sku: str = 'x,y') -> float:\n    return 0\n"
        self.assertEqual(reproduction._estimate_arity("f", source), 2)

    def test_function_not_found_returns_none(self):
        source = "def other_function():\n    pass\n"
        self.assertIsNone(reproduction._estimate_arity("missing_function", source))


class ExtractParamsTests(unittest.TestCase):
    def test_single_param_with_type(self):
        source = "def average(nums: list[float]) -> float:\n    return sum(nums) / len(nums)\n"
        params = reproduction._extract_params("average", source)
        self.assertEqual(params, [{"name": "nums", "type": "list[float]"}])

    def test_two_differently_typed_params(self):
        source = "def get_line_item_price(catalog: dict[str, float], sku: str) -> float:\n    return catalog[sku]\n"
        params = reproduction._extract_params("get_line_item_price", source)
        self.assertEqual(
            params,
            [{"name": "catalog", "type": "dict[str, float]"}, {"name": "sku", "type": "str"}],
        )

    def test_param_without_type_annotation(self):
        source = "def average(nums):\n    return 0\n"
        params = reproduction._extract_params("average", source)
        self.assertEqual(params, [{"name": "nums", "type": None}])

    def test_default_value_with_comma_in_string_not_mistaken_for_separator(self):
        source = "def f(catalog: dict[str, float], sku: str = 'x,y') -> float:\n    return 0\n"
        params = reproduction._extract_params("f", source)
        self.assertEqual(len(params), 2)
        self.assertEqual(params[1]["name"], "sku")


class ValidateNamedArgsTests(unittest.TestCase):
    def setUp(self):
        self.params = [{"name": "catalog", "type": "dict[str, float]"}, {"name": "sku", "type": "str"}]

    def test_rejects_non_dict(self):
        self.assertIsNone(reproduction._validate_named_args(["a", "b"], self.params))

    def test_rejects_missing_key(self):
        self.assertIsNone(reproduction._validate_named_args({"catalog": {}}, self.params))

    def test_accepts_matching_keys_and_orders_positionally(self):
        # deliberately out of order to prove it re-orders by the real parameter order
        result = reproduction._validate_named_args({"sku": "widget", "catalog": {"widget": 1.0}}, self.params)
        self.assertEqual(result, [{"widget": 1.0}, "widget"])


class ModuleImportNameTests(unittest.TestCase):
    def test_resolves_dotted_path_relative_to_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / "mini_repo").mkdir()
            target = workspace / "mini_repo" / "calculator.py"
            target.write_text("def average(nums):\n    return 0\n")
            name = reproduction._module_import_name(str(target), workspace)
            self.assertEqual(name, "mini_repo.calculator")

    def test_returns_none_for_path_outside_workspace(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as other:
            workspace = Path(tmp)
            outside_file = Path(other) / "evil.py"
            outside_file.write_text("x = 1\n")
            self.assertIsNone(reproduction._module_import_name(str(outside_file), workspace))


if __name__ == "__main__":
    unittest.main()
