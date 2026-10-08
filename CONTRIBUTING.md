# CONTRIBUTING

## RESOURCES

If you wish to contribute to this project, please be sure to read/subscribe to the following resources:

- [Coding Standards](https://peps.python.org/pep-0008/)
- [Code of Conduct](CODE_OF_CONDUCT.md)

## BRANCHING AND RELEASES

### `main` is the development branch

`main` is the live, bleeding-edge branch. It is kept working (all tests pass
and coverage stays at 100% for each service) but it may contain features that
are only partly delivered. **Do not run `main` in production** - use a tagged
release instead.

### One service per branch

Keep each branch and pull request to a single service, and prefix the title
with the service, e.g. `[CMS] Test case types`, `[Gateway] Membership
enforcement`, `[Portal] Project membership`. This keeps reviews small, lets
each service's CI run independently, and makes changes easy to revert.

A feature that spans services is delivered as a series of branches, normally
in dependency order:

1. **CMS / Identity** - the service that owns the data and defines the API.
2. **Gateway** - proxy routes for the new API.
3. **Portal** - the user interface.

Settle the API contract (request and response shapes, status codes) in the
first branch and add the requests to the Postman collection, so the later
branches have something firm to build on.

The exception is a breaking API change that cannot work with only one side
updated. Deliver those together in one pull request.

### Releases

Releases are tagged from `main` once a feature is complete across every
service it touches - not part-way through a series of branches. Users should
install a tagged release (or its Docker image), never `main`.

