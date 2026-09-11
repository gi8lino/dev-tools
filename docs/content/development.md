# Development

The repository deliberately separates executable programs from GNU Make integration.

```text
.github/workflows/   CI, release, and Pages workflows
make/                shared GNU Make modules
scripts/             executable development tools
tests/               Python unit tests
docs/content/        Lore documentation source
docs/site.toml       Lore static-site configuration
docs/site/           generated site, ignored by Git
```

## Tests

Run the complete suite with:

```sh
make test
```

Tests cover the standalone tools and the modular Make integration, including automatic module/tool downloads and version-specific caching.

## Make help

The repository dogfoods its own help and tagging modules. Show all available targets with:

```sh
make help
```

The complete target list is documented in [Make modules and targets](make-modules.md).

## Documentation

The documentation is generated with [Lore](https://github.com/gi8lino/lore) from `docs/content/` using `docs/site.toml`.

With a `lore` binary on `PATH`, build it with:

```sh
make site
```

Build for localhost and serve the result:

```sh
make site-serve
```

The default local documentation port is `8081`; override it when needed:

```sh
make site-serve SITE_PORT=8090
```

GitHub Actions downloads a pinned Lore release, builds `docs/site/`, verifies the expected static files, and deploys that directory through GitHub Pages.
