"""Unit tests for the admin-configurable merge field rules."""

import unittest
from unittest import mock

from OpenPostbud.database.common import PostType
from OpenPostbud.database.digital_post import field_rules
from OpenPostbud.database.digital_post.field_rules import FieldRule, RuleType

from tests.db_test_case import DatabaseTestCase


def _rule(field_name="Testfelt", rule_type=RuleType.NOT_CONTAINS, value="forbudt",
          apply_digital=True, apply_physical=True) -> FieldRule:
    """Build a FieldRule instance for testing.

    The boolean columns are passed explicitly because their defaults are only
    applied on flush, not on Python instantiation.
    """
    return FieldRule(
        field_name=field_name,
        rule_type=rule_type,
        value=value,
        apply_digital=apply_digital,
        apply_physical=apply_physical,
    )


class AppliesToTest(unittest.TestCase):
    """Tests for FieldRule.applies_to."""

    def test_digital_only(self):
        """A digital-only rule applies to DIGITAL and AUTO, but not PHYSICAL."""
        rule = _rule(apply_digital=True, apply_physical=False)
        self.assertTrue(rule.applies_to(PostType.DIGITAL))
        self.assertFalse(rule.applies_to(PostType.PHYSICAL))
        # AUTO applies if the rule applies to either route.
        self.assertTrue(rule.applies_to(PostType.AUTO))

    def test_physical_only(self):
        """A physical-only rule applies to PHYSICAL and AUTO, but not DIGITAL."""
        rule = _rule(apply_digital=False, apply_physical=True)
        self.assertFalse(rule.applies_to(PostType.DIGITAL))
        self.assertTrue(rule.applies_to(PostType.PHYSICAL))
        self.assertTrue(rule.applies_to(PostType.AUTO))

    def test_both(self):
        """A rule applying to both routes applies to every PostType."""
        rule = _rule(apply_digital=True, apply_physical=True)
        self.assertTrue(rule.applies_to(PostType.DIGITAL))
        self.assertTrue(rule.applies_to(PostType.PHYSICAL))
        self.assertTrue(rule.applies_to(PostType.AUTO))

    def test_neither(self):
        """A rule applying to no route applies to no PostType."""
        rule = _rule(apply_digital=False, apply_physical=False)
        self.assertFalse(rule.applies_to(PostType.DIGITAL))
        self.assertFalse(rule.applies_to(PostType.PHYSICAL))
        self.assertFalse(rule.applies_to(PostType.AUTO))


class IsSatisfiedNotContainsTest(unittest.TestCase):
    """Tests for FieldRule.is_satisfied with the NOT_CONTAINS rule type."""

    def test_absent_field_is_satisfied(self):
        """A NOT_CONTAINS rule is satisfied when its field is absent from the data."""
        rule = _rule(field_name="Testfelt", rule_type=RuleType.NOT_CONTAINS, value="forbudt")
        self.assertTrue(rule.is_satisfied({"Andet Felt": "forbudt"}))

    def test_value_without_substring_is_satisfied(self):
        """A value not containing the forbidden substring satisfies the rule."""
        rule = _rule(rule_type=RuleType.NOT_CONTAINS, value="forbudt")
        self.assertTrue(rule.is_satisfied({"Testfelt": "Helt fint indhold"}))

    def test_value_with_substring_violates(self):
        """A value containing the forbidden substring violates the rule."""
        rule = _rule(rule_type=RuleType.NOT_CONTAINS, value="forbudt")
        self.assertFalse(rule.is_satisfied({"Testfelt": "Dette er forbudt!"}))

    def test_substring_match_is_case_insensitive(self):
        """The NOT_CONTAINS substring check ignores case."""
        rule = _rule(rule_type=RuleType.NOT_CONTAINS, value="forbudt")
        self.assertFalse(rule.is_satisfied({"Testfelt": "Dette er FORBUDT"}))
        self.assertFalse(rule.is_satisfied({"Testfelt": "FoRbUdT tekst"}))

    def test_empty_field_value_is_satisfied(self):
        """An empty field value cannot contain the forbidden substring, so it is satisfied."""
        rule = _rule(rule_type=RuleType.NOT_CONTAINS, value="forbudt")
        self.assertTrue(rule.is_satisfied({"Testfelt": ""}))


class IsSatisfiedRegexMatchTest(unittest.TestCase):
    """Tests for FieldRule.is_satisfied with the REGEX_MATCH rule type."""

    def test_absent_field_is_satisfied(self):
        """A REGEX_MATCH rule is satisfied when its field is absent from the data."""
        rule = _rule(rule_type=RuleType.REGEX_MATCH, value=r"[A-Z].*")
        self.assertTrue(rule.is_satisfied({"Andet Felt": "abc"}))

    def test_full_match_is_satisfied(self):
        """A value that fully matches the pattern satisfies the rule."""
        rule = _rule(rule_type=RuleType.REGEX_MATCH, value=r"\d{4}")
        self.assertTrue(rule.is_satisfied({"Testfelt": "1234"}))

    def test_no_match_violates(self):
        """A value that does not match the pattern violates the rule."""
        rule = _rule(rule_type=RuleType.REGEX_MATCH, value=r"\d{4}")
        self.assertFalse(rule.is_satisfied({"Testfelt": "abcd"}))

    def test_partial_match_violates(self):
        """A partial match violates the rule; the whole value must match the pattern."""
        # fullmatch is required, so a value with extra characters fails.
        rule = _rule(rule_type=RuleType.REGEX_MATCH, value=r"\d{4}")
        self.assertFalse(rule.is_satisfied({"Testfelt": "12345"}))
        self.assertFalse(rule.is_satisfied({"Testfelt": "x1234"}))


class ToRowDictTest(unittest.TestCase):
    """Tests for FieldRule.to_row_dict."""

    def test_maps_fields_and_formats_booleans(self):
        """to_row_dict maps all columns and renders booleans as 'Ja'/'Nej'."""
        rule = _rule(field_name="Testfelt", rule_type=RuleType.REGEX_MATCH,
                     value=r"[A-Z].*", apply_digital=True, apply_physical=False)
        rule.id = 7

        self.assertEqual(rule.to_row_dict(), {
            "id": 7,
            "field_name": "Testfelt",
            "rule_type": RuleType.REGEX_MATCH.value,
            "value": r"[A-Z].*",
            "apply_digital": "Ja",
            "apply_physical": "Nej",
        })


class ValidateFieldDataTest(unittest.TestCase):
    """Tests for the validate_field_data send-off helper.

    get_field_rules is patched so the logic can be tested without a database.
    """

    def _patch_rules(self, rules):
        patcher = mock.patch.object(field_rules, "get_field_rules", return_value=tuple(rules))
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_no_rules_returns_none(self):
        """With no rules configured, validation passes (returns None)."""
        self._patch_rules([])
        self.assertIsNone(field_rules.validate_field_data({"Testfelt": "forbudt"}, PostType.DIGITAL))

    def test_satisfied_rule_returns_none(self):
        """A satisfied rule produces no validation message."""
        self._patch_rules([_rule(rule_type=RuleType.NOT_CONTAINS, value="forbudt")])
        self.assertIsNone(field_rules.validate_field_data({"Testfelt": "fint"}, PostType.DIGITAL))

    def test_violated_rule_returns_message(self):
        """A violated rule returns a message naming the field and rule type."""
        self._patch_rules([_rule(field_name="Testfelt", rule_type=RuleType.NOT_CONTAINS, value="forbudt")])
        message = field_rules.validate_field_data({"Testfelt": "forbudt"}, PostType.DIGITAL)
        self.assertIsNotNone(message)
        self.assertIn("Testfelt", message)
        self.assertIn(RuleType.NOT_CONTAINS.value, message)

    def test_rule_not_applicable_to_route_is_skipped(self):
        """A rule is only enforced on routes it applies to."""
        # A physical-only rule must not fail a letter sent digitally.
        self._patch_rules([_rule(value="forbudt", apply_digital=False, apply_physical=True)])
        self.assertIsNone(field_rules.validate_field_data({"Testfelt": "forbudt"}, PostType.DIGITAL))
        # ...but it should fail when sent physically.
        self.assertIsNotNone(field_rules.validate_field_data({"Testfelt": "forbudt"}, PostType.PHYSICAL))

    def test_returns_first_violation(self):
        """When multiple rules are violated, only the first violation is reported."""
        self._patch_rules([
            _rule(field_name="Felt A", rule_type=RuleType.NOT_CONTAINS, value="aaa"),
            _rule(field_name="Felt B", rule_type=RuleType.NOT_CONTAINS, value="bbb"),
        ])
        message = field_rules.validate_field_data({"Felt A": "aaa", "Felt B": "bbb"}, PostType.DIGITAL)
        self.assertIn("Felt A", message)
        self.assertNotIn("Felt B", message)

    def test_message_is_truncated_to_column_limit(self):
        """The validation message is truncated to fit the Letter.message column limit."""
        # The Letter.message column holds 100 chars; long field names must not overflow it.
        self._patch_rules([_rule(field_name="X" * 200, rule_type=RuleType.NOT_CONTAINS, value="forbudt")])
        message = field_rules.validate_field_data({"X" * 200: "forbudt"}, PostType.DIGITAL)
        self.assertLessEqual(len(message), 100)


class DatabaseCallsTest(DatabaseTestCase):
    """Tests for the database-backed field rule functions, run against an
    isolated in-memory database provided by DatabaseTestCase.
    """

    def test_get_field_rules_empty(self):
        """get_field_rules returns an empty tuple when no rules exist."""
        self.assertEqual(field_rules.get_field_rules(), ())

    def test_create_field_rule_persists_and_assigns_id(self):
        """create_field_rule persists the rule and assigns it an id."""
        rule = field_rules.create_field_rule(
            "Testfelt", RuleType.NOT_CONTAINS, "forbudt", apply_digital=True, apply_physical=False
        )
        self.assertIsNotNone(rule.id)

        stored = field_rules.get_field_rules()
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0].id, rule.id)
        self.assertEqual(stored[0].field_name, "Testfelt")
        self.assertEqual(stored[0].rule_type, RuleType.NOT_CONTAINS)
        self.assertEqual(stored[0].value, "forbudt")
        self.assertTrue(stored[0].apply_digital)
        self.assertFalse(stored[0].apply_physical)

    def test_create_multiple_field_rules(self):
        """Multiple rules can be created and are all returned by get_field_rules."""
        field_rules.create_field_rule("Felt A", RuleType.NOT_CONTAINS, "aaa", True, True)
        field_rules.create_field_rule("Felt B", RuleType.REGEX_MATCH, r"\d+", True, True)

        names = sorted(rule.field_name for rule in field_rules.get_field_rules())
        self.assertEqual(names, ["Felt A", "Felt B"])

    def test_delete_field_rule(self):
        """delete_field_rule removes an existing rule and returns True."""
        rule = field_rules.create_field_rule("Testfelt", RuleType.NOT_CONTAINS, "forbudt", True, True)

        self.assertTrue(field_rules.delete_field_rule(rule.id))
        self.assertEqual(field_rules.get_field_rules(), ())

    def test_delete_only_removes_targeted_rule(self):
        """delete_field_rule removes only the targeted rule, leaving others intact."""
        keep = field_rules.create_field_rule("Behold", RuleType.NOT_CONTAINS, "x", True, True)
        remove = field_rules.create_field_rule("Fjern", RuleType.NOT_CONTAINS, "y", True, True)

        self.assertTrue(field_rules.delete_field_rule(remove.id))

        remaining = field_rules.get_field_rules()
        self.assertEqual([rule.id for rule in remaining], [keep.id])

    def test_delete_nonexistent_returns_false(self):
        """Deleting a non-existent rule id returns False."""
        self.assertFalse(field_rules.delete_field_rule(999))


if __name__ == "__main__":
    unittest.main()
