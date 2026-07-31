# codex-swap

Switch between multiple Codex CLI accounts without repeatedly logging out and
back in.

Save personal and work accounts as named profiles, activate either one by
name, or toggle to the next profile with a single command.

> **Inspired by
> [`realiti4/claude-swap`](https://github.com/realiti4/claude-swap).** Its
> friendly multi-account workflow inspired this project. `codex-swap` is an
> independent implementation for OpenAI Codex and is not affiliated with that
> project or its maintainers.

## Features

- Save the current Codex login under a memorable name.
- Enroll another account without logging out or invalidating the active one.
- Switch directly to `personal`, `work`, or any other saved profile.
- Toggle through profiles by running `codex-swap switch` without a name.
- Preserve refreshed credentials when leaving the active profile.
- Refuse to overwrite a live login that is not associated with a saved
  profile unless `--force` is explicit.
- Inspect profiles with human-readable or JSON output.
- Protect credential files with private permissions, locking, and atomic
  replacement.
- Use only the Python standard library—no package dependencies.

`codex-swap` intentionally does not use undocumented Codex quota endpoints, so
it does not provide usage dashboards or automatic rate-limit rotation.

## Requirements

- macOS or Linux
- Python 3.10 or newer
- [Codex CLI](https://developers.openai.com/codex/cli) installed and available
  as `codex`

## Installation

### curl (quickest)

Install the pinned `0.2.0` release to `/usr/local/bin`:

```sh
sudo curl -fsSL \
  https://raw.githubusercontent.com/irangarcia/codex-swap/0.2.0/codex-swap \
  -o /usr/local/bin/codex-swap
sudo chmod 755 /usr/local/bin/codex-swap
```

Verify the installation:

```sh
codex-swap --version
```

### Homebrew (macOS and Linux)

```sh
brew install irangarcia/tap/codex-swap
```

Upgrade later releases with:

```sh
brew upgrade codex-swap
```

### From source

Clone this repository and run its installer:

```sh
git clone https://github.com/irangarcia/codex-swap.git
cd codex-swap
chmod +x codex-swap install.sh
./install.sh
```

The installer copies the executable to `~/.local/bin/codex-swap`. To use a
different location:

```sh
CODEX_SWAP_INSTALL_DIR=/your/bin ./install.sh
```

If `~/.local/bin` is not already in your `PATH`, add this to `~/.zshrc` or the
equivalent file for your shell:

```sh
export PATH="$HOME/.local/bin:$PATH"
```

Open a new terminal and verify the installation:

```sh
codex-swap --version
```

## Quick start

### 1. Save your current account

If Codex is already signed into your personal account:

```sh
codex-swap add personal
```

### 2. Add your work account

```sh
codex-swap login work
```

Complete the Codex browser sign-in with your work account. The login happens
inside an isolated temporary `CODEX_HOME`; your personal session is never
logged out.

### 3. Switch accounts

Choose a specific profile:

```sh
codex-swap switch personal
codex-swap switch work
```

Or rotate to the next saved profile:

```sh
codex-swap switch
```

`use` is an alias for `switch`:

```sh
codex-swap use personal
```

Start a new Codex session after switching. The Codex CLI and IDE extension
share cached login details, so restart or reopen an existing extension session
when you need it to pick up the new account immediately.

## Usage

### List profiles

```sh
codex-swap list
```

The active profile is marked with `*`:

```text
  personal         personal@example.com
* work             work@example.com
```

For machine-readable output:

```sh
codex-swap list --json
```

### Show the active profile

```sh
codex-swap status
codex-swap status --json
```

### Refresh or replace a profile

If Codex reports that a refresh token was revoked or expired, sign into that
account again and replace its saved credentials:

```sh
codex-swap login personal --force
```

The active account is left untouched unless the new login succeeds.

### Remove a profile

```sh
codex-swap remove personal
```

Removing the active profile is blocked by default. To remove only its saved
snapshot while leaving the current Codex login in place:

```sh
codex-swap remove personal --force
```

After this command, the live login is intentionally untracked. A subsequent
switch is blocked until you save it with `codex-swap add NAME` or explicitly
allow replacement with `codex-swap switch PROFILE --force`.

## Command reference

```text
codex-swap add NAME [--force]       Save the current Codex login
codex-swap login NAME [--force]     Sign in separately and save the account
codex-swap switch [NAME] [--force]  Activate NAME, or rotate when omitted
codex-swap use [NAME] [--force]     Alias for switch
codex-swap list [--json]            List saved profiles
codex-swap status [--json]          Show the active profile
codex-swap remove NAME [--force]    Delete a saved profile snapshot
codex-swap rm NAME [--force]        Alias for remove
codex-swap --version                Print the installed version
```

Run `codex-swap COMMAND --help` for command-specific options.

## How it works

Codex caches file-based login credentials in `auth.json` under `CODEX_HOME`,
which defaults to `~/.codex`. See the official
[Codex authentication documentation](https://learn.chatgpt.com/docs/auth) for
details about login caching and credential storage.

When you add or switch an account, `codex-swap`:

1. Takes an inter-process lock so two switches cannot overlap.
2. Saves the active `auth.json` back to its profile, preserving any refresh
   token updates Codex made during use.
3. Refuses to overwrite an existing live login when there is no active-profile
   marker, unless `--force` was supplied.
4. Writes the selected profile to the live Codex credential path using atomic
   file replacement.
5. Records which named profile is active.

When you run `codex-swap login NAME`, the browser login uses a temporary,
isolated `CODEX_HOME`. It never runs `codex logout`, because logging out can
leave a previously captured OAuth session unusable.

Only Codex's local authentication file is switched. ChatGPT browser sessions,
desktop-app accounts, and workspace policies are outside this tool's scope.

## Data locations

| Data                   | Default location                                        |
| ---------------------- | ------------------------------------------------------- |
| Codex live credentials | `${CODEX_HOME:-~/.codex}/auth.json`                     |
| Saved profiles         | `${XDG_DATA_HOME:-~/.local/share}/codex-swap/profiles/` |
| Active-profile marker  | `${XDG_DATA_HOME:-~/.local/share}/codex-swap/active`    |
| Switch lock            | `${XDG_DATA_HOME:-~/.local/share}/codex-swap/.lock`     |
| Installed executable   | `~/.local/bin/codex-swap`                               |

Set `CODEX_SWAP_HOME` to move all profile data and metadata to another
directory:

```sh
export CODEX_SWAP_HOME="$HOME/.codex-swap"
```

## Security

Saved profiles contain OAuth access and refresh tokens. Treat the
`codex-swap` data directory like a password:

- Never commit it to Git.
- Never paste its files into issues, chats, or support tickets.
- Do not sync it to an untrusted cloud drive.
- Back it up only to encrypted storage you control.

Profile files and metadata use `0600` permissions. Data directories use
`0700`. Writes are atomic, and profile names are validated before being used
as paths.

Managed Codex environments can enforce a login method or workspace. This tool
cannot bypass those controls.

## Troubleshooting

### `Your refresh token was revoked`

Refresh the affected profile:

```sh
codex-swap login PROFILE --force
```

Then activate it and restart Codex:

```sh
codex-swap switch PROFILE
```

### `codex_apps` returns HTTP 401 after switching

The selected profile likely contains expired or revoked credentials. Refresh
it with `codex-swap login PROFILE --force`, then fully restart Codex so MCP
clients initialize with the new session.

### The IDE extension still shows the previous account

Close and reopen the Codex extension session. The CLI and extension share the
credential cache, but an already-running process may still hold the previous
session in memory.

### `codex-swap` is not found

Confirm that the installation directory is in `PATH`:

```sh
export PATH="$HOME/.local/bin:$PATH"
```

## Development

Run the test suite:

```sh
python3 -m unittest discover -s tests -v
```

Tests use temporary directories and fake credentials; they do not read or
modify your real Codex login.

Project layout:

```text
codex-swap       Standalone Python CLI
install.sh       Local installer
tests/           Unit and regression tests
README.md        Documentation
LICENSE          MIT license
```

## License

`codex-swap` is available under the [MIT License](LICENSE).

## Inspiration

This project is inspired by
[`realiti4/claude-swap`](https://github.com/realiti4/claude-swap), a
multi-account switcher for Claude Code. Its straightforward account setup,
named switching, status commands, and user-focused documentation shaped the
experience of `codex-swap`.
