CREATE TABLE "Letters_new" (
	id VARCHAR(12) NOT NULL,
	shipment_id VARCHAR(12),
	recipient_id BINARY NOT NULL,
	updated_at DATETIME NOT NULL,
	status VARCHAR(9) NOT NULL,
	message VARCHAR(100),
	field_data BINARY NOT NULL,
	transaction_id VARCHAR,
	sent_as VARCHAR(8),
	post_type VARCHAR(8) NOT NULL DEFAULT 'DIGITAL',
	created_by VARCHAR(50) NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(shipment_id) REFERENCES "Shipments" (id) ON DELETE CASCADE
)


INSERT INTO "Letters_new" (id, shipment_id, recipient_id, updated_at, status, message, field_data, transaction_id, sent_as, post_type, created_by)
SELECT id, shipment_id, recipient_id, updated_at, status, message, field_data, transaction_id, sent_as,
	COALESCE((SELECT post_type FROM "Shipments" WHERE "Shipments".id = "Letters".shipment_id), 'DIGITAL'),
	COALESCE((SELECT created_by FROM "Shipments" WHERE "Shipments".id = "Letters".shipment_id), 'unknown')
FROM "Letters"


DROP TABLE "Letters"


ALTER TABLE "Letters_new" RENAME TO "Letters"
