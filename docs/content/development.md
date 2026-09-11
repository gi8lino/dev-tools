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

Build it with:

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

`make site` and `make site-serve` use `github-release-install` to install the pinned Lore release into `bin/` when needed. The helper detects the current macOS/Linux architecture, keeps the concrete binary as `bin/lore-<tag>`, and maintains `bin/lore` as the stable symlink. No system-wide Lore installation is required.

GitHub Actions uses the same `make site` path, so CI also builds exclusively with the pinned Lore GitHub release before deploying `docs/site/` through GitHub Pages.
