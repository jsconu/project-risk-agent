# Releasing

Releases are published to PyPI via [Trusted Publishing][trusted-publishing], so
no PyPI API token is stored in this repository. `.github/workflows/publish.yml`
builds the package and publishes it whenever a GitHub Release is published.

## One-time setup (maintainer)

The `project-risk-agent` project does not exist on PyPI yet, so the first
publish uses a **pending publisher** rather than a token — PyPI creates the
project automatically the first time the linked workflow publishes.

1. On [pypi.org][pypi], go to **Your account → Publishing**
   (`https://pypi.org/manage/account/publishing/`).
2. Under "Add a new pending publisher", fill in:
   - PyPI Project Name: `project-risk-agent`
   - Owner: `jsconu`
   - Repository name: `project-risk-agent`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`
3. Click **Add**.
4. In this repository's GitHub settings, create an environment named `pypi`
   (Settings → Environments → New environment). No secrets are needed there.

See PyPI's [guide to creating a project through OIDC][oidc-create] for
background on the pending-publisher flow.

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
[oidc-create]: https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/
