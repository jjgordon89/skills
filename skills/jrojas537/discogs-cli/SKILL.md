---
name: discogs-cli
description: Manages a user's vinyl record collection on Discogs. Use it to list records or folders from a collection.
metadata: {"clawdbot":{"emoji":"Vinyl","requires":{"bins":["go"]}}}
---

# Discogs Collection Manager

This skill provides a command-line interface to interact with a user's record collection on Discogs.com. It uses a subcommand structure similar to `git` or `gog`.

## Prerequisites

This skill is a Go program and requires the Go toolchain to be installed and compiled.

**Installation (Debian/Ubuntu):**
`sudo apt-get update && sudo apt-get install -y golang-go`

## One-Time Setup

Before first use, you must compile the tool, ensure the resulting binary is in the system's PATH, and configure your credentials.

1.  **Compile the tool:**
    Navigate to the `scripts` directory inside the skill and run the Go build command.
    ```bash
    cd <path_to_skill>/scripts && go build -o discogs-cli .
    ```

2.  **Install the tool:**
    Move the compiled `discogs-cli` binary to a location in the system's PATH, such as `/usr/local/bin`.

3.  **Configure Credentials:**
    This command saves your Discogs token and username to a configuration file (`~/.config/discogs-cli/config.yaml`).
    ```bash
    discogs-cli config set -u "YourUsername" -t "YourSecretToken"
    ```

## Usage

Once the binary is compiled and in the system's PATH, you can run the following commands.

### Fetch Album Art

Downloads the album art for a given release and displays it in the chat.

```bash
discogs-cli release art <release_id>
```

### List Collection Folders

Shows all folders and their record counts.

```bash
discogs-cli collection list-folders
```

### List Releases in a Folder

Shows all records within a specific folder. The output is a formatted table.

```bash
# List all releases from the "All" folder (default)
discogs-cli collection list

# List all releases from a specific folder by ID
discogs-cli collection list --folder 8815833
```

## Search the Discogs Database

Search for releases, artists, or labels.

```bash
# Search for a release (default type)
discogs-cli search "Daft Punk - Discovery"

# Search for an artist
discogs-cli search --type artist "Aphex Twin"
```

## Manage Your Wantlist

Work with your Discogs wantlist.

### List Your Wantlist

Displays all items in your wantlist.

```bash
discogs-cli wantlist list
```

### Add to Your Wantlist

Adds a release to your wantlist by its ID.

```bash
discogs-cli wantlist add 12345
```

### Remove from Your Wantlist

Removes a release from your wantlist by its ID.

```bash
discogs-cli wantlist remove 12345
```

## Caching and Valuation Commands

These commands rely on a local cache for performance. The user must run `sync` first to populate the cache.

### Sync Collection Details (Slow)

Fetches detailed data for every item in the collection and builds a local cache. This command is slow and should be run in the background. Inform the user that this will take time.

```bash
discogs-cli collection sync
```

### Get Collection Value (Fast)

Reads the local cache to provide the estimated market value for each item and the total collection. This command is fast. If it fails, the cache is likely missing, and the user needs to run the `sync` command.

```bash
discogs-cli collection value
```

### Get Single Release Details (Fast)

Provides a detailed view of a single release, including tracklist.

```bash
discogs-cli collection get 35198584
```
