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
   package to PyPI, and `build-apps.yml`, which builds the double-click
   downloads for non-technical users and attaches them to the release.

## Desktop app downloads

`build-apps.yml` produces `ProjectRiskAgent-Windows.exe` and
`ProjectRiskAgent-macOS.zip` (Apple silicon). Each build must pass the app's
`--self-test` before it is uploaded. To try the builds without cutting a
release, run the workflow manually from the Actions tab and download the
artifacts. The apps are unsigned; see [chat-app.md](chat-app.md) for what
that means for users and what signing would require.

The README's quick start links to the downloads on the latest release, so
publish a release (and confirm both files are attached) before promoting it.

[trusted-publishing]: https://docs.pypi.org/trusted-publishers/
[pypi]: https://pypi.org/
[oidc-create]: https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/
