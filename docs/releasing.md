# Releasing

Releases are published to PyPI via [Trusted Publishing][trusted-publishing], so
no PyPI API token is stored in this repository. `.github/workflows/publish.yml`
builds the package and publishes it whenever a GitHub Release is published.

## One-time setup (maintainer, on pypi.org)

1. Create the `project-risk-agent` project on [PyPI][pypi] (the first publish
   can also register it, but pre-creating it lets you configure trusted
   publishing before the first release).
2. On the project's PyPI page, go to **Publishing** and add a trusted
   publisher:
   - Owner: `jsconu`
   - Repository: `project-risk-agent`
   - Workflow: `publish.yml`
   - Environment: `pypi`
3. In this repository's GitHub settings, create an environment named `pypi`
   (Settings → Environments). No secrets are needed there.

## Cutting a release

1. Move the relevant `[Unreleased]` entries in `CHANGELOG.md` into a new
   version section.
2. Bump the version in `pyproject.toml` and `src/project_risk_agent/__init__.py`
   to match.
3. Commit, then tag: `git tag vX.Y.Z && git push origin vX.Y.Z`.
4. Create a GitHub Release from that tag (Releases → Draft a new release).
   Publishing the release triggers `publish.yml`, which builds and uploads the
   package to PyPI.

[trusted-publishing]: https://docs.pypi.org/trusted-publishers/
[pypi]: https://pypi.org/
