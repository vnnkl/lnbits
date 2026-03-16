# Specification: Add npub Identifier Support to Notifications

## Overview

This feature extends LNbits notification settings to support **npub (Nostr public key)** identifiers in addition to the existing NIP-05 identifiers (e.g., `user@domain.com`). When a user enters an npub, the system will validate it, fetch the user's relay list using NIP-65 (Relay List Metadata), and deliver notifications via Nostr DM to those relays. This enables more flexible, standards-aligned Nostr support and allows users to receive LNbits notifications directly via their Nostr public keys without requiring a NIP-05 domain setup.

## Workflow Type

**Type**: feature

**Rationale**: This is a new capability being added to an existing notification system. It requires:
- Backend logic for npub detection and NIP-65 relay fetching
- Modifications to the notification dispatch flow
- UI updates to clarify that both npub and NIP-05 formats are accepted
- New tests for the added functionality

## Task Scope

### Services Involved
- **main** (primary) - LNbits backend Python service with FastAPI, handles notification dispatch
- **frontend** (integration) - Vue/Quasar UI components for notification settings

### This Task Will:
- [ ] Add npub format detection to notification identifier processing
- [ ] Implement NIP-65 relay list fetching for npub identifiers
- [ ] Update `send_nostr_notification()` to support both npub and NIP-05 flows
- [ ] Update UI labels/hints to indicate both formats are accepted
- [ ] Add unit tests for npub validation and NIP-65 relay fetching
- [ ] Add integration test for end-to-end npub notification flow

### Out of Scope:
- Changes to non-Nostr notification methods (Telegram, Email, Push)
- General notification system refactoring
- NIP-05 backward compatibility changes (existing NIP-05 flow must continue to work)
- Changes to how notifications are stored/queued

## Service Context

### Main Backend Service

**Tech Stack:**
- Language: Python 3.10+
- Framework: FastAPI
- ORM: SQLAlchemy
- Key directories:
  - `lnbits/core/services/` - Business logic services
  - `lnbits/utils/` - Utility functions
  - `lnbits/templates/` - Vue templates
  - `tests/` - Test suite

**Entry Point:** `lnbits/__main__.py`

**How to Run:**
```bash
poetry install
poetry run python -m lnbits
```

**Port:** 5002

**API Documentation:** http://localhost:5002/docs

## Files to Modify

| File | Service | What to Change |
|------|---------|---------------|
| `lnbits/core/services/nostr.py` | backend | Add `fetch_nip65_relays(pubkey_hex: str)` function to query bootstrap relays for kind:10002 events |
| `lnbits/core/services/notifications.py` | backend | Update `send_nostr_notification()` to detect npub format and route to NIP-65 relay lookup |
| `lnbits/templates/pages/account.vue` | frontend | Update hint text to indicate both npub and NIP-05 formats are accepted |
| `lnbits/static/i18n/en.js` | frontend | Update `notifications_nostr_identifier_desc` translation to mention npub support |

## Files to Reference

These files show patterns to follow:

| File | Pattern to Copy |
|------|----------------|
| `lnbits/utils/nostr.py` | npub validation with `validate_pub_key()`, conversion with `normalize_public_key()` |
| `lnbits/core/services/nostr.py` | Async HTTP/WebSocket pattern, `fetch_nip5_details()` structure |
| `lnbits/templates/components/admin/notifications.vue` | Quasar input field patterns for notification settings |
| `tests/unit/test_helpers.py` | Unit test structure and patterns |

## Patterns to Follow

### npub Validation Pattern

From `lnbits/utils/nostr.py`:

```python
def validate_pub_key(pubkey: str) -> str:
    if pubkey.startswith("npub"):
        _, data = bech32_decode(pubkey)
        if data:
            decoded_data = convertbits(data, 5, 8, False)
            if decoded_data:
                pubkey = bytes(decoded_data).hex()
    try:
        _hex = bytes.fromhex(pubkey)
    except Exception as exc:
        raise ValueError("Pubkey must be in npub or hex format.") from exc

    if len(_hex) != 32:
        raise ValueError("Pubkey length incorrect.")

    return pubkey
```

**Key Points:**
- Already handles both npub and hex formats
- Returns hex format in all cases
- Validates 32-byte length requirement
- Use this function for npub validation

### NIP-05 Relay Fetch Pattern

From `lnbits/core/services/nostr.py`:

```python
async def fetch_nip5_details(identifier: str) -> tuple[str, list[str]]:
    identifier, domain = identifier.split("@")
    # ... validation ...
    url = f"https://{domain}/.well-known/nostr.json?name={identifier}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
        # ... extract pubkey and relays ...
        return pubkey, relays
```

**Key Points:**
- Returns tuple of (pubkey_hex, relay_list)
- Uses httpx.AsyncClient for HTTP requests
- Validates response data before returning
- New NIP-65 function should follow similar return pattern

### WebSocket Connection Pattern

From `lnbits/core/services/nostr.py`:

```python
ws_connections: list[WebSocket] = []
for relay in relays:
    try:
        ws = create_connection(relay, timeout=2)
        ws.send(notification)
        ws_connections.append(ws)
    except Exception as e:
        logger.warning(f"Error sending notification to relay {relay}: {e}")
await asyncio.sleep(1)
for ws in ws_connections:
    ws.close()
```

**Key Points:**
- Uses `websocket.create_connection` with timeout
- Handles connection failures gracefully
- Closes connections after use
- Apply same pattern for NIP-65 relay queries

## Requirements

### Functional Requirements

1. **npub Format Detection**
   - Description: The system must detect whether an identifier is npub format (starts with "npub1") or NIP-05 format (contains "@")
   - Acceptance: Given an identifier "npub1abc...", the system routes to NIP-65 flow. Given "user@domain.com", routes to NIP-05 flow.

2. **NIP-65 Relay List Fetching**
   - Description: For npub identifiers, query bootstrap relays for kind:10002 events to get the user's relay list
   - Acceptance: Given a valid npub, returns a list of relay URLs from the user's NIP-65 event. Returns fallback relays if no NIP-65 event found.

3. **npub Validation**
   - Description: Validate npub format using existing `validate_pub_key()` function
   - Acceptance: Invalid npub formats (wrong prefix, wrong length, invalid bech32) raise ValueError with descriptive message.

4. **Backward Compatibility**
   - Description: Existing NIP-05 identifiers must continue to work unchanged
   - Acceptance: Notifications to NIP-05 identifiers work exactly as before.

5. **UI Clarity**
   - Description: Update UI hints to indicate both formats are accepted
   - Acceptance: User sees "Enter NIP-05 (user@domain.com) or npub (npub1...)" in the input field hint.

### Edge Cases

1. **No NIP-65 Event Found** - Use a fallback list of popular relays (e.g., wss://relay.damus.io, wss://nos.lol)
2. **Bootstrap Relay Timeout** - Try multiple bootstrap relays, continue if at least one responds
3. **Invalid npub Format** - Return clear validation error message
4. **Empty Relay List from NIP-65** - Use fallback relays
5. **Identifier is Both Valid** - "npub1" prefix takes precedence over checking for "@"

## Implementation Notes

### DO
- Use existing `validate_pub_key()` and `normalize_public_key()` from `lnbits/utils/nostr.py`
- Follow the async pattern from `fetch_nip5_details()` for the new NIP-65 function
- Use websocket library already imported in `nostr.py` for relay queries
- Log warnings for relay connection failures, don't fail the entire operation
- Return hex pubkey format consistently (same as NIP-05 flow)
- Use a reasonable timeout (2-5 seconds) for relay connections

### DON'T
- Don't modify the `UserNotifications` model - it already stores the identifier as a string
- Don't change the notification queue/dispatch architecture
- Don't add new dependencies - use existing libraries (websocket, bech32, etc.)
- Don't break existing NIP-05 functionality
- Don't store relay lists persistently - fetch fresh each time

### NIP-65 Bootstrap Relays

Use these relays for querying NIP-65 events:
```python
BOOTSTRAP_RELAYS = [
    "wss://relay.damus.io",
    "wss://nos.lol",
    "wss://relay.nostr.band",
    "wss://nostr.wine",
    "wss://relay.snort.social",
]
```

### NIP-65 Query Format

```python
# Request kind:10002 event for a pubkey
subscription = ["REQ", "nip65", {"kinds": [10002], "authors": [pubkey_hex], "limit": 1}]
```

### NIP-65 Response Parsing

```python
# Event structure
{
    "kind": 10002,
    "tags": [
        ["r", "wss://relay1.example.com", "read"],
        ["r", "wss://relay2.example.com", "write"],
        ["r", "wss://relay3.example.com"]  # no marker = read+write
    ]
}
# Extract relays with "write" marker or no marker for sending DMs
```

## Development Environment

### Start Services

```bash
# Install dependencies
poetry install

# Run LNbits
poetry run python -m lnbits

# Run tests
poetry run pytest tests/
```

### Service URLs
- LNbits: http://localhost:5002
- API Docs: http://localhost:5002/docs

### Required Environment Variables
- `LNBITS_NOSTR_NOTIFICATIONS_ENABLED`: Set to "true" to enable Nostr notifications
- `LNBITS_NOSTR_NOTIFICATIONS_PRIVATE_KEY`: Server's nsec private key for sending DMs

## Success Criteria

The task is complete when:

1. [ ] Users can enter npub identifiers in notification settings (user-level in account.vue)
2. [ ] npub identifiers are validated on the backend
3. [ ] NIP-65 relay list is fetched for npub identifiers
4. [ ] Notifications are successfully sent via Nostr DM to npub recipients
5. [ ] Existing NIP-05 identifier flow continues to work unchanged
6. [ ] UI hints clearly indicate both formats are accepted
7. [ ] No console errors during npub notification flow
8. [ ] All existing tests still pass
9. [ ] New unit tests cover npub validation and NIP-65 fetching

## QA Acceptance Criteria

**CRITICAL**: These criteria must be verified by the QA Agent before sign-off.

### Unit Tests
| Test | File | What to Verify |
|------|------|----------------|
| `test_is_npub_format` | `tests/unit/test_nostr.py` | Correctly identifies npub vs NIP-05 formats |
| `test_validate_npub_valid` | `tests/unit/test_nostr.py` | Valid npub passes validation |
| `test_validate_npub_invalid` | `tests/unit/test_nostr.py` | Invalid npub raises ValueError |
| `test_fetch_nip65_relays` | `tests/unit/test_nostr.py` | Returns relay list from mocked NIP-65 event |
| `test_fetch_nip65_fallback` | `tests/unit/test_nostr.py` | Returns fallback relays when no NIP-65 event |

### Integration Tests
| Test | Services | What to Verify |
|------|----------|----------------|
| `test_send_nostr_notification_npub` | backend | Full flow: npub → validate → fetch relays → send DM |
| `test_send_nostr_notification_nip05` | backend | Existing NIP-05 flow still works |
| `test_nostr_notification_invalid_identifier` | backend | Invalid identifiers raise appropriate errors |

### End-to-End Tests
| Flow | Steps | Expected Outcome |
|------|-------|------------------|
| npub Notification Flow | 1. Enter valid npub in account settings 2. Save 3. Trigger notification | Nostr DM sent to relays from NIP-65 |
| NIP-05 Backward Compatibility | 1. Enter NIP-05 identifier 2. Save 3. Trigger notification | Existing flow works unchanged |
| Invalid Format Handling | 1. Enter invalid npub/NIP-05 2. Attempt to send | Clear error message returned |

### Browser Verification (if frontend)
| Page/Component | URL | Checks |
|----------------|-----|--------|
| Account Settings | `http://localhost:5002/account` | Notifications tab shows updated hint text |
| Account Settings | `http://localhost:5002/account` | npub can be entered and saved |

### Database Verification (if applicable)
| Check | Query/Command | Expected |
|-------|---------------|----------|
| User settings stored | Query user extra.notifications | nostr_identifier field contains npub value |

### QA Sign-off Requirements
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All E2E tests pass
- [ ] Browser verification complete
- [ ] No regressions in existing NIP-05 notification functionality
- [ ] Code follows established patterns from reference files
- [ ] No security vulnerabilities introduced (input validation for npub)
- [ ] Error messages are user-friendly and descriptive

## Technical Implementation Details

### New Function: `is_npub_format(identifier: str) -> bool`

Location: `lnbits/core/services/nostr.py`

```python
def is_npub_format(identifier: str) -> bool:
    """Check if identifier is an npub (starts with npub1) vs NIP-05 (contains @)"""
    return identifier.startswith("npub1")
```

### New Function: `fetch_nip65_relays(pubkey_hex: str) -> list[str]`

Location: `lnbits/core/services/nostr.py`

```python
async def fetch_nip65_relays(pubkey_hex: str) -> list[str]:
    """
    Fetch relay list from NIP-65 event for a given pubkey.
    Queries bootstrap relays for kind:10002 events.
    Returns write-capable relays, or fallback list if none found.
    """
    # Implementation details in code
```

### Updated Function: `send_nostr_notification(identifier: str, message: str)`

Location: `lnbits/core/services/notifications.py`

```python
async def send_nostr_notification(identifier: str, message: str):
    if is_npub_format(identifier):
        # npub flow: validate, convert to hex, fetch NIP-65 relays
        user_pubkey = validate_pub_key(identifier)
        relays = await fetch_nip65_relays(user_pubkey)
    else:
        # NIP-05 flow: existing behavior
        user_pubkey, relays = await fetch_nip5_details(identifier)

    # Send DM using existing send_nostr_dm function
    await send_nostr_dm(server_private_key, user_pubkey, message, relays)
```
