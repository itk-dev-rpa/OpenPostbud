CREATE TABLE "FieldRules" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(20) NOT NULL,
    value VARCHAR(500) NOT NULL,
    apply_digital BOOLEAN NOT NULL DEFAULT 1,
    apply_physical BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL
)
