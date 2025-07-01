# Api

Documentation for this section.

## POST /chatgpt/suggestion

Generate a ChatGPT suggestion for a feedback item.

**Request Body:**
```
{
  "feedback_id": 123,
  "temperature": 0.2 // optional, default 0.2
}
```

**Response:**
```
{
  "suggestion": "..."
}
```

- `temperature` controls the randomness/creativity of the response (0.2 = focused, 1.0 = creative).
- Returns the generated suggestion as a string.

**Example:**
```
curl -X POST http://localhost:8000/chatgpt/suggestion \
  -H "Content-Type: application/json" \
  -d '{"feedback_id": 123, "temperature": 0.2}'
```
