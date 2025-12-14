# OpenAI Authentication Verification

## Testing with Real API Key

To verify your OpenAI API key works correctly, run this curl command:

```bash
# Test 1: List available models (basic auth check)
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models

# Test 2: With organization and project (if configured)
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     -H "OpenAI-Organization: $OPENAI_ORGANIZATION" \
     -H "OpenAI-Project: $OPENAI_PROJECT" \
     https://api.openai.com/v1/models
```

### Expected Response (Success)
```json
{
  "object": "list",
  "data": [
    {"id": "gpt-4o", "object": "model", ...},
    {"id": "gpt-4o-mini", "object": "model", ...},
    {"id": "o3-mini", "object": "model", ...},
    ...
  ]
}
```

### Expected Response (401 Unauthorized)
```json
{
  "error": {
    "message": "Incorrect API key provided...",
    "type": "invalid_request_error",
    "param": null,
    "code": "invalid_api_key"
  }
}
```

## Environment Variables

The AI Router uses the following environment variables for OpenAI authentication:

| Variable | Purpose | Required |
|---|---|---|
| `OPENAI_API_KEY` | Primary API key (fallback) | No (local-only if missing) |
| `OPENAI_API_KEY_TIER2` | Preferred API key | No |
| `OPENAI_BASE_URL` | Custom base URL | No (default: https://api.openai.com/v1) |
| `OPENAI_ORGANIZATION` | Organization ID | No |
| `OPENAI_PROJECT` | Project ID | No |

**Priority**: `OPENAI_API_KEY_TIER2` > `OPENAI_API_KEY`

## Troubleshooting 401 Errors

If you see `401 Unauthorized` errors:

1. **Check API Key Format**
   - Must start with `sk-`
   - No extra spaces or quotes
   - Verify in `.env.local` or environment

2. **Verify Key Permissions**
   - Log into https://platform.openai.com/api-keys
   - Check if key has access to required models
   - Verify organization/project settings

3. **Test with Curl**
   - Run the curl command above
   - If curl fails, the key is invalid
   - If curl succeeds but router fails, check router config

4. **Check Organization/Project**
   - If using org/project IDs, verify they match your account
   - Try without org/project first to isolate the issue

## Router Behavior

- **No API Key**: Router runs in local-only mode (Ollama)
- **Valid Key**: Cloud models validated and available for routing
- **401 Error**: Cloud disabled automatically, all requests route to local models
- **Cached Auth**: After first validation (success or failure), result is cached for 5 minutes to avoid spam
