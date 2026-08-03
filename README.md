# Integrated Test Management Suite (ITEMS)

ITEMS is a web-based test management tool written in Python that can be used by software development teams to manage, track, and organize software testing efforts. It helps teams create and manage test cases, execute test runs, track test results, and generate detailed reports and analytics.

## News  

### 3rd August 2026
The current Alpha release is [V0.1.0](https://github.com/SwatKat1977/items/releases/tag/V0.1.0)

IMPORTANT: The current Alpha is not production ready/safe and is currently an early preview.

### Previous News
- Important Information: The version is currently at V0.0.0 [MVP] on the main branch
whilst we are still in early development.
- Follow the [changelog](ChangeLog) for new features and bug fixes.

Currently, there are no nightly or release Docker images for the ITEMS services.
This is on the TODO list.

## Documentation

- [Getting Started (PLACEHOLDER)](https://github.com)
- [Building (PLACEHOLDER)](https://github.com)
- [Running via Docker (PLACEHOLDER)](https://github.com)
- [Roadmap (PLACEHOLDER)](https://github.com)

## Development

The following Python libraries are required to run ITEMS locally:
- quart
- jsonschema
- requests
- tzlocal
- aiohttp

### Accounts Service

Python packages:
- quart
- aiohttp
- jsonschema
- requests
- bcrypt

### Contents Management System (CMS) Service

To build the docker image:
```
./scripts/dev/createDockerCMS.sh <tag>

e.g.
./scripts/dev/createDockerCMS.sh v0.0.1
```

To run/start the docker image:
```
./scripts/dev/runCmsDocker.sh <config file> <db file> <tag>

e.g.
./scripts/dev/runCmsDocker.sh configs/cms.cfg databases/items_cms.LATEST.db latest
```

### Gateway Service

Python packages:
- quart
- tzlocal
