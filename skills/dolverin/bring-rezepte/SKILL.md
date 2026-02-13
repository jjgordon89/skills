---
name: bring-shopping
description: Use when running the OpenClaw/ClawHub Bring! skill to search recipes on the web, parse recipe URLs for ingredients, and add ingredients to a Bring shopping list. Covers recipe search via web_search, URL parsing, recipe batch-add, list management, and inspiration filters.
---

# Bring App

## When to Use

- User fragt nach Rezeptvorschlägen oder saisonalen Gerichten ("Was essen wir heute?", "Rezeptideen", "saisonale Inspirationen")
- User möchte Einkaufslisten anzeigen oder aktualisieren ("Was steht auf der Einkaufsliste?", "Füge ... hinzu")
- User will Zutaten für ein Rezept hinzufügen
- User fragt nach Bring-Liste-Status oder Rezept-Markern
- Jegliche Anfragen rund um Einkaufsplanung und Rezeptauswahl

## Overview

Build a Bring! CLI-focused skill that uses the updated `node-bring-api` to fetch inspirations (recipes), highlight seasonal dishes, and add user-selected ingredients to a shopping list.

## Quick start workflow

1. List inspiration filters and identify seasonal tags.
2. Fetch inspirations using those tags.
3. Summarize 3-7 seasonal dishes.
4. Ask which dishes to add to a list, then add their ingredients (not the dish name).

Use `references/bring-inspirations.md` for endpoint details and headers.
These scripts load `node-bring-api` from:

1. `BRING_NODE_API_PATH` (if set), or
2. `../../node-bring-api/build/bring.js` relative to this skill, or
3. the installed `bring-shopping` package.

## Tasks

### 1) Discover available filters (season, diet, cuisine)

Run:

```
node scripts/bring_inspirations.js --filters
```

- Read the JSON and pick tags that look seasonal (e.g., winter/sommer/fruehling/herbst).
- If unsure, ask the user to pick from the filter list.

### 2) Fetch inspirations

Run:

```
node scripts/bring_inspirations.js --tags "<comma-separated-tags>" --limit 20
```

- If the user did not specify tags, default to `mine`.
- Inspect the JSON and extract a short list of suggested dishes with any available metadata.
- Capture `content.contentSrcUrl` for each dish (needed to load ingredients).

### 3) Suggest seasonal dishes

- Return 3-7 options.
- Include dish name and 1 short sentence (if available in the JSON).
- Ask the user which dishes should be added to the list.

### 4) Add selected dishes to a list (ingredients only)

If the user confirms, list available lists if needed:

```
node scripts/bring_list.js --lists
```

Add ingredients from the selected dish content URL(s):

```
node scripts/bring_list.js --list <list-uuid> --content-url "https://api.getbring.com/rest/v2/bringtemplates/content/<uuid>"
```

Or resolve by list name:

```
node scripts/bring_list.js --list-name "Einkauf" --content-url "https://api.getbring.com/rest/v2/bringtemplates/content/<uuid>"
```

## List Management (v2.2.0)

Create a new shopping list:

```
node scripts/bring_list.js --create-list "Amazon"
```

Returns the new list's UUID and name. If a list with that name already exists, returns the existing list info without creating a duplicate.

Note: List deletion is not supported by the Bring API — lists can only be deleted via the Bring app.

## Environment

These scripts default to ENV values:

- `BRING_EMAIL`
- `BRING_PASSWORD`
- `BRING_COUNTRY` (default `DE`)
- `BRING_NODE_API_PATH` (optional path to `build/bring.js`)

If ENV is not set, pass `--email` and `--password` explicitly.

## Recipe Markers (v2.1.0)

Add items tagged with a recipe name so you can track which ingredients belong to which recipe:

```
node scripts/bring_list.js --list-name "Einkauf" --add-recipe "Lasagne" --recipe-items "Nudeln,Hackfleisch,Tomaten"
```

This stores each item with the specification `[Rezept] Lasagne`, acting as a recipe marker.

List distinct recipe markers on a list:

```
node scripts/bring_list.js --list-name "Einkauf" --recipe-markers
```

Returns a sorted array of recipe names currently on the list.

## Recipe Search & URL Parsing (v2.2.0)

### Workflow: Rezeptvorschläge machen

When a user asks for recipe suggestions ("Was soll ich heute kochen?", "Rezeptideen für Sommer"):

**Step 1: Search for recipes**
Use your `web_search` tool (Brave API) to find recipe URLs:

```
web_search("Sommer Rezepte vegetarisch site:chefkoch.de")
web_search("schnelle Abendessen Rezepte site:chefkoch.de OR site:lecker.de")
```

Pick 3-5 promising recipe URLs from the search results.

**Step 2: Parse recipe URLs for structured data**

```
node scripts/bring_inspirations.js --parse-url "url1,url2,url3"
```

Returns structured JSON per recipe: name, ingredients (itemId + spec), image URL, source URL.
For a single URL, returns a single object. For multiple URLs, returns an array.

**Step 3: Present options to the user**
Show the user the parsed recipes with:

- Recipe name
- Number of ingredients
- Source URL
- Key ingredients (first 5-6)

Ask which recipe(s) to add to the shopping list.

**Step 4: Add selected recipe to list**

```
node scripts/bring_list.js --list-name "Einkauf" --add-recipe-url "https://www.chefkoch.de/rezepte/123/lasagne.html"
```

This parses the recipe, creates a marker (e.g., `=== LASAGNE ===`), tags all ingredients with the recipe name, and batch-adds everything to the list.

### Parse recipe URL (standalone)

```
node scripts/bring_inspirations.js --parse-url "https://www.chefkoch.de/rezepte/123/lasagne.html"
```

Returns structured ingredient data without adding to any list. Useful for previewing.

### Supported recipe sites

The Bring parser supports most major recipe websites including:

- chefkoch.de
- lecker.de
- eatsmarter.de
- kitchenstories.com
- And many more (any site with structured recipe data / JSON-LD)

## Notes

- Keep the skill output in German for Germany by default.
- Do not add items without explicit user confirmation.
- Always add ingredients instead of the dish name when using inspirations.

## Resources

### scripts/

- `scripts/bring_inspirations.js`: Log in and call inspirations and filter endpoints.
- `scripts/bring_list.js`: List available shopping lists and add items.

### references/

- `references/bring-inspirations.md`: Endpoint details and headers.
