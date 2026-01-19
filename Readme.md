# Hospital Bulk Processing Service

## Run
```bash
docker compose up --build
```

## Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/hospitals/bulk` | Upload CSV, returns batch_id |
| GET | `/hospitals/bulk/{batch_id}/status` | Check progress |
| GET | `/hospitals/bulk/{batch_id}/results` | Get final results |
| POST | `/hospitals/bulk/{batch_id}/retry` | Retry failed rows |
| WS | `/ws/bulk/{batch_id}` | Real-time progress |

## CSV Format
```
name,address,phone
Apollo Hospital,Chennai,044-123456
```
Required: `name`, `address` | Optional: `phone` | Max: 20 rows
