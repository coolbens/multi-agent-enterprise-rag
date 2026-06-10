# API Documentation

## Auth
- `POST /auth/register`
- `POST /auth/login`

## Documents
- `POST /documents/upload` multipart form field: `files`
- `GET /documents/list`
- `DELETE /documents/delete/{id}`

## Chat
- `POST /chat/ask`
```json
{"question":"What is the HR leave policy?", "top_k":5}
```
- `GET /chat/history`
- `DELETE /chat/history/{message_id}`
- `DELETE /chat/history` clear current user history

## Admin
- `GET /admin/dashboard`

FastAPI Swagger UI is available at:
`http://localhost:8000/docs`
