# Integrated Test Management Suite (ITEMS)

ITEMS is a web-based test management tool written in Python that can be used by software development teams to manage, track, and organize software testing efforts. It helps teams create and manage test cases, execute test runs, track test results, and generate detailed reports and analytics.

## News  

### 25th October 2026
The current Alpha release is [V0.5.0](https://github.com/SwatKat1977/items/releases/tag/V0.5.0)

IMPORTANT: The current Alpha is not production ready/safe and is currently an early preview.

### Previous News
- Nightly Docker images are built from `main` for each service (tagged
`NIGHTLY`) and published to
[Docker Hub](https://hub.docker.com/r/swatkat1977/items). They are
development builds - use a tagged release for anything else.

### Which version should I use?

The `main` branch is the live development branch and may contain unfinished
features. For anything other than development, use a
[tagged release](https://github.com/SwatKat1977/items/releases). See
[CONTRIBUTING](CONTRIBUTING.md) for how branches and releases work.

## Documentation

- [Getting Started](https://github.com/SwatKat1977/items/wiki/Getting-Started)
- [Building from source](https://github.com/SwatKat1977/items/wiki/Building-ITEMS-from-source)
- [Running via Docker](https://github.com/SwatKat1977/items/wiki/Running-via-Docker)
- [Roadmap](https://github.com/SwatKat1977/items/wiki/Roadmap)

## Running with Docker over HTTPS

With Docker Compose, ITEMS is served over HTTPS by a Caddy container
(`https_proxy`). Browse to `https://localhost`. Plain `http://` on port 80 is
redirected, and the Web Portal itself is not exposed.

- **First visit on your own machine:** Caddy makes its own certificate, so
  the browser shows a warning. To trust it once, copy the root certificate out
  and add it to your system trust store:
  `docker cp https_proxy:/data/caddy/pki/authorities/local/root.crt .`
- **A real site:** set `ITEMS_DOMAIN=your.domain.name` in `.env`. The name
  must point at the machine and ports 80 and 443 must be reachable; Caddy then
  gets and renews a trusted certificate automatically.
- **Without Docker:** the Web Portal runs plain HTTP unless you add a `[tls]`
  section to its config. See `configs/web_portal.cfg`.

## Contributing

See [CONTRIBUTING](CONTRIBUTING.md) for the branching and release process,
and the [Code of Conduct](CODE_OF_CONDUCT.md).

## License

ITEMS is released under the [Apache 2.0 License](LICENSE).
