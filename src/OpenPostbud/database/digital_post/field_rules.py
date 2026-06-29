"""This module contains the FieldRule ORM class and admin-configurable
merge field validation rules.

Unlike the hardcoded MemoFields in `letters.py`, these rules are managed by
admins at runtime and are enforced at send-off (in the shipment worker), not
during shipment creation.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
import re

from sqlalchemy import String, select
from sqlalchemy.orm import Mapped, mapped_column

from OpenPostbud.database.base import Base
from OpenPostbud.database import connection
from OpenPostbud.database.common import PostType


class RuleType(Enum):
    """The kind of check a FieldRule performs on a field's value.

    NOT_CONTAINS: The field value must not contain the rule value (case-insensitive).
    REGEX_MATCH: The field value must fully match the rule value as a regex pattern.
    """
    NOT_CONTAINS = "Må ikke indeholde"
    REGEX_MATCH = "Skal matche mønster"


class FieldRule(Base):
    """An ORM class representing an admin-configured merge field rule."""
    __tablename__ = "FieldRules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    field_name: Mapped[str] = mapped_column(String(255))
    rule_type: Mapped[RuleType]
    value: Mapped[str] = mapped_column(String(500))
    apply_digital: Mapped[bool] = mapped_column(default=True)
    apply_physical: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    def applies_to(self, post_type: PostType) -> bool:
        """Whether this rule should be checked for the given post type.

        AUTO applies the rule if it applies to either route, so the letter is
        checked whichever route a recipient takes.
        """
        if post_type == PostType.DIGITAL:
            return self.apply_digital
        if post_type == PostType.PHYSICAL:
            return self.apply_physical
        return self.apply_digital or self.apply_physical

    def is_satisfied(self, field_data: dict[str, str]) -> bool:
        """Whether the given merge data satisfies this rule.

        A rule on a field that is absent from the data is considered satisfied,
        mirroring the MemoFields pattern matching behavior.
        """
        if self.field_name not in field_data:
            return True

        value = field_data[self.field_name]

        if self.rule_type == RuleType.NOT_CONTAINS:
            return self.value.lower() not in value.lower()
        if self.rule_type == RuleType.REGEX_MATCH:
            return re.fullmatch(self.value, value) is not None
        return True

    def to_row_dict(self) -> dict[str, str]:
        """Convert to a dictionary to be shown in a table."""
        return {
            "id": self.id,
            "field_name": self.field_name,
            "rule_type": self.rule_type.value,
            "value": self.value,
            "apply_digital": "Ja" if self.apply_digital else "Nej",
            "apply_physical": "Ja" if self.apply_physical else "Nej",
        }


def get_field_rules() -> tuple[FieldRule]:
    """Get all field rules in the database."""
    with connection.get_session() as session:
        result = session.execute(select(FieldRule)).scalars()
        return tuple(result)


def create_field_rule(field_name: str, rule_type: RuleType, value: str, apply_digital: bool, apply_physical: bool) -> FieldRule:
    """Add a new field rule to the database.

    Args:
        field_name: The name of the merge field column the rule checks.
        rule_type: The kind of check to perform.
        value: The substring or regex pattern the check uses.
        apply_digital: Whether the rule applies to Digital Post.
        apply_physical: Whether the rule applies to Fysisk Post.

    Returns:
        The created field rule.
    """
    rule = FieldRule(
        field_name=field_name,
        rule_type=rule_type,
        value=value,
        apply_digital=apply_digital,
        apply_physical=apply_physical,
    )

    with connection.get_session() as session:
        session.add(rule)
        session.commit()

    return rule


def delete_field_rule(rule_id: int) -> bool:
    """Delete the field rule with the given id.

    Returns:
        True if a rule was deleted, False if no rule was found.
    """
    with connection.get_session() as session:
        rule = session.get(FieldRule, rule_id)
        if rule:
            session.delete(rule)
            session.commit()
            return True
        return False


def validate_field_data(field_data: dict[str, str], route: PostType) -> str | None:
    """Validate merge data against all applicable field rules.

    Args:
        field_data: The letter's merge data.
        route: The concrete route the letter is being sent as (DIGITAL or PHYSICAL).

    Returns:
        A short error message for the first violated rule, or None if all rules pass.
    """
    for rule in get_field_rules():
        if rule.applies_to(route) and not rule.is_satisfied(field_data):
            # Keep within the Letter.message column limit (100 chars).
            return f"Regel overtrådt: {rule.field_name} - {rule.rule_type.value}"[:100]
    return None
