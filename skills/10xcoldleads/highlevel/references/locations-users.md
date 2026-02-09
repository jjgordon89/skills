# Locations & Users API Reference

## Locations — `/locations/`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/locations/{locationId}` | Get location details |
| PUT | `/locations/{locationId}` | Update location |
| GET | `/locations/search?companyId={id}` | Search locations (Agency) |
| POST | `/locations/` | Create sub-account (Agency) |
| DELETE | `/locations/{locationId}` | Delete sub-account (Agency) |
| GET | `/locations/timeZones` | List all time zones |
| GET | `/locations/{id}/customValues` | List custom values |
| POST/PUT/DELETE | `/locations/{id}/customValues/...` | Custom value CRUD |
| GET | `/locations/{id}/customFields` | List custom fields |
| POST/PUT/DELETE | `/locations/{id}/customFields/...` | Custom field CRUD |
| GET | `/locations/{id}/tags` | List tags |
| POST/PUT/DELETE | `/locations/{id}/tags/...` | Tag CRUD |
| GET | `/locations/{id}/templates` | List templates |
| GET | `/locations/{id}/tasks/search` | Search location tasks |

**Scopes**: `locations.readonly`, `locations.write` (Agency), `locations/customValues.*`, `locations/customFields.*`, `locations/tags.*`, `locations/templates.readonly`, `locations/tasks.readonly`

## Users — `/users/`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/users/?locationId={id}` | List users |
| GET | `/users/{userId}` | Get user |
| POST | `/users/` | Create user |
| PUT | `/users/{userId}` | Update user |
| DELETE | `/users/{userId}` | Delete user |

**Filters**: companyId, email, status
**Note**: Agency users cannot be created via API

**Scopes**: `users.readonly`, `users.write`
