# API Testing Pattern for port-scanner-002

## Pattern: API Testing as a Step-5 Validation

When a task involves a backend service (FastAPI/Flask/etc.), adding a step-5 where Tester directly calls HTTP APIs is the correct way to validate the fix. This is distinct from code review (step-4) — step-5 tests real behavior, not code structure.

## When to Use

- Task has a running HTTP service (FastAPI, Flask, etc.)
- Fix is behavioral (performance, response correctness, error handling)
- Code review alone cannot confirm the fix works

## port-scanner-002 Example

### TC Design for a Concurrency Bug Fix

| TC | Purpose | Key Assertion |
|----|---------|--------------|
| TC-1 | Health check | status=healthy |
| TC-2 | Basic scan | returns all fields |
| TC-3 | **Concurrency** (key) | 6 ports scan in < 6s |
| TC-4 | Validation: missing params | HTTP 422 |
| TC-5 | Validation: invalid IP | HTTP 422 |
| TC-6 | Port range parsing | total_ports correct |

**TC-3 is the critical test** — it directly measures whether the concurrency fix (asyncio.to_thread) works. Code review can confirm the fix is present; API test confirms it works.

## Key Insight: Concurrency Tests Can Be Flaky

When testing concurrency fixes:
- `asyncio.to_thread` uses `ThreadPoolExecutor` with `max_workers=CPU_count`
- 13 ports × 1s timeout = ~1s if fully concurrent
- But: measured time from HTTP request includes entire request/response cycle
- Always measure from the API response (`scan_time_ms`) not wall-clock time
- Threshold should be: `port_count * 0.5 * timeout` (e.g., 13 ports → < 6.5s)

## Test Script Pattern

```python
# Use requests (not httpx) — simpler, fewer async issues
import requests
import json

BASE_URL = "http://localhost:8080"

def tc3_concurrency():
    payload = {"ip": "8.8.8.8", "ports": "22,53,80,443,3306,5432", "rate": 5000}
    resp = requests.post(f"{BASE_URL}/api/scan", json=payload, timeout=30)
    data = resp.json()
    scan_time = data.get("scan_time_ms", 0) / 1000  # convert to seconds
    port_count = data.get("total_ports", 0)
    threshold = port_count * 0.5  # 50% of serial time
    return scan_time < threshold, scan_time, port_count
```

## Setup Requirements

Before running API tests:
1. Ensure service is running (`curl /health` returns 200)
2. Clear `__pycache__` if code was modified
3. Restart service after code changes (uvicorn doesn't auto-reload in production mode)
4. Use subprocess + timeout, not background=True (clean lifecycle management)

## Common Pitfalls

- **TC timeout too short**: Set timeout=30+ for scan tests (socket timeout is 1s/port)
- **Measuring wall-clock instead of scan_time_ms**: Always use `scan_time_ms` from response
- **Service not restarted**: Old code still in memory after file change
- **File:// vs http://**: For static file servers (dashboard.html), use Playwright; for API services, use requests against http://localhost:PORT
