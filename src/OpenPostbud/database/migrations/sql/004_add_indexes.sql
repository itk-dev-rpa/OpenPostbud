CREATE INDEX letters_shipment_id ON "Letters"(shipment_id)


CREATE INDEX letters_transaction_id ON "Letters"(transaction_id)


CREATE INDEX letters_status ON "Letters"(status)


CREATE INDEX nemsms_messages_shipment_id ON "NemSMS_Messages"(shipment_id)


CREATE INDEX nemsms_messages_transaction_id ON "NemSMS_Messages"(transaction_id)


CREATE INDEX nemsms_messages_status ON "NemSMS_Messages"(status)


CREATE INDEX registration_tasks_job_id ON "RegistrationTasks"(job_id)


CREATE INDEX registration_tasks_status ON "RegistrationTasks"(status)