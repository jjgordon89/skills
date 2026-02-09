#!/usr/bin/env python3
"""GoHighLevel API v2 Helper — supports all 39 endpoint groups.
Usage: python3 ghl-api.py <command> [args...]

Environment:
  HIGHLEVEL_TOKEN       — Private Integration Bearer token (required)
  HIGHLEVEL_LOCATION_ID — Sub-account Location ID (required)

Base URL: https://services.leadconnectorhq.com
All requests include: Authorization: Bearer <token>, Version: 2021-07-28
"""

import json, os, sys, time, urllib.request, urllib.error, urllib.parse

BASE = "https://services.leadconnectorhq.com"
TOKEN = os.environ.get("HIGHLEVEL_TOKEN", "")
LOC_ID = os.environ.get("HIGHLEVEL_LOCATION_ID", "")
VERSION = "2021-07-28"
MAX_RETRIES = 3


def _headers():
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Version": VERSION,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _request(method, path, body=None, retries=MAX_RETRIES):
    """Make API request with retry logic for 429/5xx errors."""
    url = f"{BASE}{path}" if path.startswith("/") else f"{BASE}/{path}"
    data = json.dumps(body).encode() if body else None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers=_headers(), method=method)
            with urllib.request.urlopen(req) as resp:
                raw = resp.read().decode()
                return json.loads(raw) if raw else {"status": resp.status}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode() if e.fp else ""
            if e.code == 429 and attempt < retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"Rate limited (429). Retrying in {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            if e.code >= 500 and attempt < retries - 1:
                time.sleep(2)
                continue
            return {"error": e.code, "message": err_body}
        except Exception as ex:
            return {"error": str(ex)}
    return {"error": "Max retries exceeded"}


def _get(path):
    return _request("GET", path)


def _post(path, body=None):
    return _request("POST", path, body)


def _put(path, body=None):
    return _request("PUT", path, body)


def _delete(path):
    return _request("DELETE", path)


def _out(data):
    print(json.dumps(data, indent=2))


# ──────────────────────────────────────────────
# Setup & Connection
# ──────────────────────────────────────────────

def test_connection():
    """Verify token and location ID are working."""
    if not TOKEN:
        return {"error": "HIGHLEVEL_TOKEN not set. Run /highlevel-setup for instructions."}
    if not LOC_ID:
        return {"error": "HIGHLEVEL_LOCATION_ID not set. Run /highlevel-setup for instructions."}
    result = _get(f"/locations/{LOC_ID}")
    if "error" in result:
        return result
    loc = result.get("location", result)
    return {
        "status": "connected",
        "locationName": loc.get("name", "Unknown"),
        "locationId": LOC_ID,
        "address": loc.get("address", ""),
        "timezone": loc.get("timezone", ""),
    }


# ──────────────────────────────────────────────
# Contacts
# ──────────────────────────────────────────────

def search_contacts(query="", limit=20):
    """Search contacts by name, email, phone, or company."""
    params = urllib.parse.urlencode({"locationId": LOC_ID, "query": query, "limit": limit})
    return _get(f"/contacts/?{params}")


def get_contact(contact_id):
    """Get full contact details by ID."""
    return _get(f"/contacts/{contact_id}")


def create_contact(data):
    """Create a new contact. data = JSON with firstName, lastName, email, phone, etc."""
    if isinstance(data, str):
        data = json.loads(data)
    data["locationId"] = LOC_ID
    return _post("/contacts/", data)


def update_contact(contact_id, data):
    """Update contact fields. data = JSON with fields to update."""
    if isinstance(data, str):
        data = json.loads(data)
    return _put(f"/contacts/{contact_id}", data)


def delete_contact(contact_id):
    """Delete a contact by ID."""
    return _delete(f"/contacts/{contact_id}")


def upsert_contact(data):
    """Create or update contact by email/phone match."""
    if isinstance(data, str):
        data = json.loads(data)
    data["locationId"] = LOC_ID
    return _post("/contacts/upsert", data)


def add_contact_tags(contact_id, tags):
    """Add tags to a contact. tags = JSON array of tag strings."""
    if isinstance(tags, str):
        tags = json.loads(tags)
    return _post(f"/contacts/{contact_id}/tags", {"tags": tags})


def remove_contact_tags(contact_id, tags):
    """Remove tags from a contact."""
    if isinstance(tags, str):
        tags = json.loads(tags)
    return _delete(f"/contacts/{contact_id}/tags")


# ──────────────────────────────────────────────
# Conversations & Messaging
# ──────────────────────────────────────────────

def list_conversations(limit=20):
    """List recent conversations."""
    params = urllib.parse.urlencode({"locationId": LOC_ID, "limit": limit})
    return _get(f"/conversations/search?{params}")


def get_conversation(conversation_id):
    """Get a specific conversation."""
    return _get(f"/conversations/{conversation_id}")


def send_message(contact_id, message, msg_type="SMS"):
    """Send a message to a contact. msg_type: SMS, Email, WhatsApp, FB, IG, Live_Chat."""
    body = {
        "type": msg_type,
        "contactId": contact_id,
        "message": message,
    }
    return _post("/conversations/messages", body)


# ──────────────────────────────────────────────
# Calendars & Appointments
# ──────────────────────────────────────────────

def list_calendars():
    """List all calendars for this location."""
    params = urllib.parse.urlencode({"locationId": LOC_ID})
    return _get(f"/calendars/?{params}")


def get_free_slots(calendar_id, start_date, end_date):
    """Get available booking slots. Dates in YYYY-MM-DD format."""
    params = urllib.parse.urlencode({
        "startDate": start_date,
        "endDate": end_date,
    })
    return _get(f"/calendars/{calendar_id}/free-slots?{params}")


def create_appointment(calendar_id, data):
    """Create a calendar appointment."""
    if isinstance(data, str):
        data = json.loads(data)
    data["calendarId"] = calendar_id
    data["locationId"] = LOC_ID
    return _post("/calendars/events", data)


# ──────────────────────────────────────────────
# Opportunities & Pipelines
# ──────────────────────────────────────────────

def list_opportunities(pipeline_id=None, limit=20):
    """List opportunities. Optionally filter by pipeline."""
    params = {"locationId": LOC_ID, "limit": limit}
    if pipeline_id:
        params["pipelineId"] = pipeline_id
    return _get(f"/opportunities/search?{urllib.parse.urlencode(params)}")


def get_opportunity(opp_id):
    """Get opportunity by ID."""
    return _get(f"/opportunities/{opp_id}")


def create_opportunity(data):
    """Create a new opportunity."""
    if isinstance(data, str):
        data = json.loads(data)
    data["locationId"] = LOC_ID
    return _post("/opportunities/", data)


def list_pipelines():
    """List all pipelines and their stages."""
    return _get(f"/opportunities/pipelines?locationId={LOC_ID}")


# ──────────────────────────────────────────────
# Workflows & Campaigns
# ──────────────────────────────────────────────

def list_workflows():
    """List all workflows."""
    return _get(f"/workflows/?locationId={LOC_ID}")


def add_to_workflow(contact_id, workflow_id):
    """Add a contact to a workflow."""
    return _post(f"/contacts/{contact_id}/workflow/{workflow_id}", {
        "eventStartTime": ""
    })


def remove_from_workflow(contact_id, workflow_id):
    """Remove a contact from a workflow."""
    return _delete(f"/contacts/{contact_id}/workflow/{workflow_id}")


def list_campaigns():
    """List all campaigns."""
    return _get(f"/campaigns/?locationId={LOC_ID}")


# ──────────────────────────────────────────────
# Invoices
# ──────────────────────────────────────────────

def list_invoices(limit=20):
    """List invoices."""
    params = urllib.parse.urlencode({"locationId": LOC_ID, "limit": limit})
    return _get(f"/invoices/?{params}")


def get_invoice(invoice_id):
    """Get invoice details."""
    return _get(f"/invoices/{invoice_id}")


def create_invoice(data):
    """Create a new invoice."""
    if isinstance(data, str):
        data = json.loads(data)
    data["altId"] = LOC_ID
    data["altType"] = "location"
    return _post("/invoices/", data)


# ──────────────────────────────────────────────
# Payments
# ──────────────────────────────────────────────

def list_orders(limit=20):
    """List payment orders."""
    params = urllib.parse.urlencode({"locationId": LOC_ID, "limit": limit})
    return _get(f"/payments/orders/?{params}")


def list_transactions(limit=20):
    """List payment transactions."""
    params = urllib.parse.urlencode({"locationId": LOC_ID, "limit": limit})
    return _get(f"/payments/transactions/?{params}")


def list_subscriptions(limit=20):
    """List payment subscriptions."""
    params = urllib.parse.urlencode({"locationId": LOC_ID, "limit": limit})
    return _get(f"/payments/subscriptions/?{params}")


# ──────────────────────────────────────────────
# Products
# ──────────────────────────────────────────────

def list_products(limit=20):
    """List products."""
    params = urllib.parse.urlencode({"locationId": LOC_ID, "limit": limit})
    return _get(f"/products/?{params}")


def get_product(product_id):
    """Get product details."""
    return _get(f"/products/{product_id}")


# ──────────────────────────────────────────────
# Forms, Surveys, Funnels
# ──────────────────────────────────────────────

def list_forms():
    """List all forms."""
    return _get(f"/forms/?locationId={LOC_ID}")


def list_form_submissions(form_id, limit=20):
    """Get form submissions."""
    params = urllib.parse.urlencode({"locationId": LOC_ID, "limit": limit})
    return _get(f"/forms/submissions?{params}&formId={form_id}")


def list_surveys():
    """List all surveys."""
    return _get(f"/surveys/?locationId={LOC_ID}")


def list_funnels():
    """List all funnels."""
    return _get(f"/funnels/funnel/list?locationId={LOC_ID}")


# ──────────────────────────────────────────────
# Social Media Planner
# ──────────────────────────────────────────────

def list_social_posts(limit=20):
    """List social media posts."""
    return _post(f"/social-media-posting/{LOC_ID}/posts/list", {
        "limit": limit, "skip": 0
    })


def create_social_post(data):
    """Create a social media post."""
    if isinstance(data, str):
        data = json.loads(data)
    return _post(f"/social-media-posting/{LOC_ID}/posts", data)


# ──────────────────────────────────────────────
# Media, Users, Links
# ──────────────────────────────────────────────

def list_media():
    """List media files."""
    return _get(f"/medias/files?locationId={LOC_ID}")


def list_users():
    """List users for this location."""
    return _get(f"/users/?locationId={LOC_ID}")


def list_trigger_links():
    """List trigger links."""
    return _get(f"/links/?locationId={LOC_ID}")


# ──────────────────────────────────────────────
# Custom Request — Access ANY v2 Endpoint
# ──────────────────────────────────────────────

def custom_request(method, path, body=None):
    """Make any API v2 request. method=GET/POST/PUT/DELETE, path starts with /."""
    if body and isinstance(body, str):
        body = json.loads(body)
    return _request(method.upper(), path, body)


# ──────────────────────────────────────────────
# CLI Router
# ──────────────────────────────────────────────

COMMANDS = {
    "test_connection": lambda: test_connection(),
    "search_contacts": lambda: search_contacts(sys.argv[2] if len(sys.argv) > 2 else ""),
    "get_contact": lambda: get_contact(sys.argv[2]),
    "create_contact": lambda: create_contact(sys.argv[2]),
    "update_contact": lambda: update_contact(sys.argv[2], sys.argv[3]),
    "delete_contact": lambda: delete_contact(sys.argv[2]),
    "upsert_contact": lambda: upsert_contact(sys.argv[2]),
    "add_contact_tags": lambda: add_contact_tags(sys.argv[2], sys.argv[3]),
    "list_conversations": lambda: list_conversations(),
    "get_conversation": lambda: get_conversation(sys.argv[2]),
    "send_message": lambda: send_message(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "SMS"),
    "list_calendars": lambda: list_calendars(),
    "get_free_slots": lambda: get_free_slots(sys.argv[2], sys.argv[3], sys.argv[4]),
    "create_appointment": lambda: create_appointment(sys.argv[2], sys.argv[3]),
    "list_opportunities": lambda: list_opportunities(),
    "get_opportunity": lambda: get_opportunity(sys.argv[2]),
    "create_opportunity": lambda: create_opportunity(sys.argv[2]),
    "list_pipelines": lambda: list_pipelines(),
    "list_workflows": lambda: list_workflows(),
    "add_to_workflow": lambda: add_to_workflow(sys.argv[2], sys.argv[3]),
    "remove_from_workflow": lambda: remove_from_workflow(sys.argv[2], sys.argv[3]),
    "list_campaigns": lambda: list_campaigns(),
    "list_invoices": lambda: list_invoices(),
    "get_invoice": lambda: get_invoice(sys.argv[2]),
    "create_invoice": lambda: create_invoice(sys.argv[2]),
    "list_orders": lambda: list_orders(),
    "list_transactions": lambda: list_transactions(),
    "list_subscriptions": lambda: list_subscriptions(),
    "list_products": lambda: list_products(),
    "get_product": lambda: get_product(sys.argv[2]),
    "list_forms": lambda: list_forms(),
    "list_form_submissions": lambda: list_form_submissions(sys.argv[2]),
    "list_surveys": lambda: list_surveys(),
    "list_funnels": lambda: list_funnels(),
    "list_social_posts": lambda: list_social_posts(),
    "create_social_post": lambda: create_social_post(sys.argv[2]),
    "list_media": lambda: list_media(),
    "list_users": lambda: list_users(),
    "list_trigger_links": lambda: list_trigger_links(),
    "custom_request": lambda: custom_request(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None),
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Commands: {', '.join(sorted(COMMANDS.keys()))}")
        sys.exit(1)
    _out(COMMANDS[sys.argv[1]]())
