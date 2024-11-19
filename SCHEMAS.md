# Database Schemas

## Shipments

Shipments that has been created in the ui.

| Column      | Type     | Note          |
| ----------- | -------- | ------------- |
| id          | int      | PK            |
| name        | str      |               |
| description | str      |               |
| template_id | int      | FK(templates) |
| created_at  | datetime |               |
| created_by  | str      |               |
| status      | str      |               |
| type        | str      | NemSMS/DP     |
|             |          |               |

## Letters

Descriptions of each letter inside shipments.

| Column       | Type     | Note          |
| ------------ | -------- | ------------- |
| id           | int      | PK            |
| shipment_id  | int      | FK(shipments) |
| recipient_id | int      |               |
| updated_at   | datetime |               |
| status       | str      |               |
| field_data   | str      | json          |
|              |          |               |

## Templates

Docx templates used to generate letters.

| Column      | Type | Note |
| ----------- | ---- | ---- |
| id          | int  | PK   |
| file_name   | str  |      |
| file_data   | blob |      |
| field_names | str  |      |
