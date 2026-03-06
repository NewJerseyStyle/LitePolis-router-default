# LitePolis Router Default

A drop-in backend for the [Polis 1.0](https://github.com/CivicTechTo/polis) frontend, built on the [LitePolis](https://github.com/NewJerseyStyle/LitePolis) infrastructure.

If you're running a Polis instance (the civic engagement platform with opinion clustering) and want a lightweight, modular backend, this package provides the full `/api/v3/*` API surface that Polis clients expect — including `client-admin`, `client-participation`, and `client-report`.

## What This Is

`litepolis-router-default` is an API router package for LitePolis. It handles authentication, conversations, participants, comments, votes, and invites — everything the Polis frontend needs to function.

## Prerequisites

- Python 3.10+
- [LitePolis](https://github.com/NewJerseyStyle/LitePolis) installed (`pip install litepolis`)

## Deploy with LitePolis

The recommended way to use this package is through `litepolis-cli`, which manages all router and database packages for you.

LitePolis uses a `packages.txt` file (like `requirements.txt`) to declare which packages your deployment needs. The default location is `~/.litepolis/packages.txt`. You can add into the `packages.txt` file instead of using `litepolis-cli deploy`.

**1. Install the LitePolis CLI**

```bash
pip install litepolis
```

**2. Confirm this router is in your deployment**

`litepolis-router-default` is included by default if you install with `litepolis[default]`. You can verify:

```bash
litepolis-cli deploy list-deps
```

If it's not listed, add it:

```bash
litepolis-cli deploy add-deps litepolis-router-default
```

**3. Initialize configuration**

```bash
litepolis-cli deploy init-config
```

Edit the generated config file to set your secret key and other settings:

```bash
nano ~/.litepolis/config.conf
```

**4. Start the server**

```bash
litepolis-cli deploy serve
```

Your Polis-compatible API will be available at `http://localhost:8000/api/v3/`.

You can now point any Polis frontend (e.g. the CivicTechTo/polis clients) at this URL as the backend.

## Configuration

Key settings in `~/.litepolis/config.conf`:

| Setting | Default | Description |
|---|---|---|
| `jwt_secret` | `dev-secret-key` | **Change this in production** |
| `jwt_expire_hours` | `168` | Token lifetime (7 days) |
| `LITEPOLIS_PORT` | `8000` | Port to serve on |

## Connecting a Polis Frontend

Once your LitePolis server is running, configure the Polis frontend to point to your server's address. In the CivicTechTo/polis repo, this is typically the `API_URL` environment variable in the client configuration.

The API base path is:
```
http://<your-server>:<port>/api/v3
```

## Supported Polis API Endpoints

This router implements the full Polis v3 API:

- **Auth** — register, login, logout, password reset
- **Users** — profile read/update
- **Conversations** — create, list, update, open/close
- **Participants** — join conversations, session init
- **Comments** — submit, moderate, get next for voting
- **Votes** — agree / disagree / pass
- **Invites** — create and join via invite code

> **Note:** Math/visualization endpoints (`/math/pca`, `/math/pca2`) currently return stub data. Full clustering output requires a separate math service.

## Known Limitations

- Math/PCA visualization is not yet computed (stub endpoints)
- Email notifications are not implemented
- Social/OIDC login is not yet supported

## Related

- [LitePolis](https://github.com/NewJerseyStyle/LitePolis) — the core platform
- [LitePolis Database Default](https://github.com/NewJerseyStyle/LitePolis-database-default) — the default database layer
- [Polis (CivicTechTo)](https://github.com/CivicTechTo/polis) — the frontend this router is compatible with
- [Awesome LitePolis](https://newjerseystyle.github.io/Awesome-LitePolis/) — browse available LitePolis packages

## License

See [LICENSE](./LICENSE).