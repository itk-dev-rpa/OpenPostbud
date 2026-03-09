CREATE TABLE "ApiUsers" (
	id VARCHAR NOT NULL,
	name VARCHAR NOT NULL,
	key_hash VARCHAR NOT NULL,
	created_at DATETIME NOT NULL,
	active BOOLEAN NOT NULL,
	PRIMARY KEY (id)
)


CREATE TABLE "AuditLogs" (
	id INTEGER NOT NULL,
	timestamp DATETIME NOT NULL,
	user VARCHAR NOT NULL,
	path VARCHAR NOT NULL,
	PRIMARY KEY (id)
)


CREATE TABLE "RegistrationJobs" (
	id VARCHAR(12) NOT NULL,
	name VARCHAR(50) NOT NULL,
	description VARCHAR(200) NOT NULL,
	job_type VARCHAR(12) NOT NULL,
	created_at DATETIME NOT NULL,
	created_by VARCHAR(50) NOT NULL,
	PRIMARY KEY (id)
)


CREATE TABLE "Templates" (
	id INTEGER NOT NULL,
	file_name VARCHAR(100) NOT NULL,
	file_data BLOB NOT NULL,
	field_names VARCHAR NOT NULL,
	PRIMARY KEY (id)
)


CREATE TABLE "NemSMS_Shipments" (
	id VARCHAR(13) NOT NULL,
	name VARCHAR(50) NOT NULL,
	description VARCHAR(200) NOT NULL,
	message_text VARCHAR(160) NOT NULL,
	created_at DATETIME NOT NULL,
	created_by VARCHAR(50) NOT NULL,
	deletion_date DATETIME NOT NULL,
	PRIMARY KEY (id)
)


CREATE TABLE "RegistrationTasks" (
	id VARCHAR(12) NOT NULL,
	job_id VARCHAR(12) NOT NULL,
	registrant_id BINARY NOT NULL,
	updated_at DATETIME NOT NULL,
	status VARCHAR(8) NOT NULL,
	result BOOLEAN,
	PRIMARY KEY (id),
	FOREIGN KEY(job_id) REFERENCES "RegistrationJobs" (id) ON DELETE CASCADE
)


CREATE TABLE "Shipments" (
	id VARCHAR(12) NOT NULL,
	name VARCHAR(50) NOT NULL,
	description VARCHAR(200) NOT NULL,
	template_id INTEGER NOT NULL,
	created_at DATETIME NOT NULL,
	created_by VARCHAR(50) NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(template_id) REFERENCES "Templates" (id)
)


CREATE TABLE "NemSMS_Messages" (
	id VARCHAR(13) NOT NULL,
	shipment_id VARCHAR(13) NOT NULL,
	recipient_id BINARY NOT NULL,
	updated_at DATETIME NOT NULL,
	status VARCHAR(9) NOT NULL,
	status_message VARCHAR(100),
	transaction_id VARCHAR,
	PRIMARY KEY (id),
	FOREIGN KEY(shipment_id) REFERENCES "NemSMS_Shipments" (id) ON DELETE CASCADE
)


CREATE TABLE "Letters" (
	id VARCHAR(12) NOT NULL,
	shipment_id VARCHAR(12) NOT NULL,
	recipient_id BINARY NOT NULL,
	updated_at DATETIME NOT NULL,
	status VARCHAR(9) NOT NULL,
	message VARCHAR(100),
	field_data BINARY NOT NULL,
	transaction_id VARCHAR,
	PRIMARY KEY (id),
	FOREIGN KEY(shipment_id) REFERENCES "Shipments" (id) ON DELETE CASCADE
)
