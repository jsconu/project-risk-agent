# -*- mode: python ; coding: utf-8 -*-
# Build with:  pyinstaller --noconfirm packaging/project-risk-agent.spec
# Windows: one double-clickable .exe.  macOS: a zip-able .app bundle.
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

from project_risk_agent import __version__

datas = collect_data_files("project_risk_agent")
hiddenimports = (
    collect_submodules("uvicorn")
    + collect_submodules("anyio")
    + collect_submodules("project_risk_agent")
)
excludes = ["openai", "tkinter", "pytest", "ruff", "IPython", "matplotlib", "numpy"]

a = Analysis(
    ["launcher.py"],
    pathex=[],
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=excludes,
    noarchive=False,
)
pyz = PYZ(a.pure)

if sys.platform == "darwin":
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="ProjectRiskAgent", console=False)
    coll = COLLECT(exe, a.binaries, a.datas, name="ProjectRiskAgent")
    app = BUNDLE(
        coll,
        name="Project Risk Agent.app",
        bundle_identifier="io.github.jsconu.project-risk-agent",
        version=__version__,
        info_plist={"NSHighResolutionCapable": True, "CFBundleDisplayName": "Project Risk Agent"},
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name="ProjectRiskAgent",
        console=True,
        upx=False,
    )
