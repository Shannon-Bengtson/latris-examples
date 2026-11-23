"""Rebuild every example model and render its website artifacts.

For each ``models/<slug>/`` this pipeline:

1. creates a fresh latris project in a temp dir (``latris.operations.init``),
2. runs the model's ``build.py`` (structure, evidence, parameters, analyses),
3. initialises the interpretation so claims reach the report and the story,
4. renders three self-contained artifacts with the app's ``latris_present``
   (skipped, with a warning, when it isn't installed):

   - ``dist/<slug>/report.html``   — the hosted report page (report_page)
   - ``dist/<slug>/explorer.html`` — the interactive explorer (explorer_html)
   - ``dist/<slug>/story.html``    — the scrollytelling story (story_html)

5. writes ``dist/gallery.json`` and copies ``site/index.html`` to
   ``dist/index.html`` — the gallery page latris-site serves.

Stories are AI-written (plan -> approve -> write). Without a provider key the
story step is skipped with a warning; set GEMINI_API_KEY to enable it.

Usage:
    python tools/build_all.py                     # every live model
    python tools/build_all.py --models sepsis-bn  # one model
    python tools/build_all.py --include-drafts    # drafts too
    python tools/build_all.py --keep-work         # keep the temp projects
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parent

# Git identity for the demo projects' commits (latris auto-commits everything).
os.environ.setdefault("GIT_AUTHOR_NAME", "latris-examples")
os.environ.setdefault("GIT_AUTHOR_EMAIL", "examples@latris.app")
os.environ.setdefault("GIT_COMMITTER_NAME", "latris-examples")
os.environ.setdefault("GIT_COMMITTER_EMAIL", "examples@latris.app")


def have_present() -> bool:
    try:
        import latris_present  # noqa: F401
        return True
    except ImportError:
        return False


def have_ai_key() -> bool:
    return any(os.environ.get(k) for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"))         or os.environ.get("LATRIS_AI_MOCK") == "1"


def latris_cli(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run the latris CLI inside a project."""
    return subprocess.run(["latris", *args], cwd=root, text=True, check=check,
                          capture_output=True)


def build_project(slug: str, spec_dir: Path, work: Path) -> Path:
    """Create the project and run the model's own build script."""
    from latris.operations.init import init_project

    manifest = yaml.safe_load((spec_dir / "model.yaml").read_text(encoding="utf-8"))
    root = work / slug
    init_project(root, statement=manifest["question"], name=manifest["title"])
    proc = subprocess.run([sys.executable, str(spec_dir / "build.py"), str(root)],
                          text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"build.py failed:\n{proc.stdout}\n{proc.stderr}")
    # Interpretation: claims feed both the report and the story's sources.
    latris_cli(root, "interpret", "initialise", check=False)
    latris_cli(root, "interpret", "refresh-claims", check=False)
    return root


def render_report(root: Path, manifest: dict, out: Path) -> None:
    from latris_present import report_page

    cfg = manifest.get("report", {})
    rendered = report_page.render_checkout(root, pack=cfg.get("pack", "publication"))
    html = report_page.build_page(rendered, title=cfg.get("title", manifest["title"]),
                                  expires_at=None, saved=True)
    (out / "report.html").write_text(html, encoding="utf-8")


def render_explorer(root: Path, manifest: dict, out: Path) -> bool:
    """The interactive explorer, where the model type supports one."""
    from latris.repo.layout import ProjectPaths
    from latris_present.explorer import operations as ops
    from latris_present.exporters import explorer_html

    cfg = manifest.get("explorer") or {}
    model_type = cfg.get("model_type") or manifest["formalisms"][0]
    try:
        doc, _ = ops.create_explorer(name="Website example", model_type=model_type, root=root)
        ops.update_explorer(doc.id, title=cfg.get("title", manifest["title"]),
                            intro=cfg.get("intro", ""), root=root)
    except Exception as exc:  # noqa: BLE001 — some formalisms have no explorer yet
        print(f"    explorer skipped ({model_type}): {exc}")
        return False
    (out / "explorer.html").write_text(
        explorer_html.render(ProjectPaths(root), doc.id), encoding="utf-8")
    return True


def render_story(root: Path, manifest: dict, out: Path) -> None:
    from latris.repo.layout import ProjectPaths
    from latris_present.exporters import story_html
    from latris_present.story import operations as sops

    cfg = manifest.get("story", {})
    doc, _ = sops.create_story(
        name=cfg.get("name", "Website story"), audience=cfg.get("audience", ""),
        purpose=cfg.get("purpose", ""), voice=cfg.get("voice", "conversational"),
        depth=cfg.get("depth", "standard"), root=root)
    doc, _ = sops.plan_story(doc.id, steer=cfg.get("steer") or None, root=root)
    doc, _ = sops.approve_outline(doc.id, root=root)
    doc, _ = sops.write_story(doc.id, root=root)
    if doc.plan_issues:
        print(f"    story plan issues: {doc.plan_issues}")
    (out / "story.html").write_text(
        story_html.render(ProjectPaths(root), doc.id), encoding="utf-8")


def build_one(spec_dir: Path, args: argparse.Namespace, dist: Path, work: Path) -> dict:
    manifest = yaml.safe_load((spec_dir / "model.yaml").read_text(encoding="utf-8"))
    slug = manifest["slug"]
    print(f"[{slug}] {manifest['title']}")
    out = dist / slug
    out.mkdir(parents=True, exist_ok=True)

    root = build_project(slug, spec_dir, work)
    entry = {
        "slug": slug,
        "title": manifest["title"],
        "domain": manifest["domain"],
        "formalisms": manifest["formalisms"],
        "summary": manifest["summary"],
        "question": manifest["question"],
        "featured": bool(manifest.get("featured", False)),
        "artifacts": {},
    }
    if args.present:
        render_report(root, manifest, out)
        entry["artifacts"]["report"] = f"{slug}/report.html"
        if render_explorer(root, manifest, out):
            entry["artifacts"]["explorer"] = f"{slug}/explorer.html"
        if args.stories:
            render_story(root, manifest, out)
            entry["artifacts"]["story"] = f"{slug}/story.html"
        else:
            print("    story skipped (no AI provider key)")
    else:
        print("    rendering skipped (latris_present not installed)")
    return entry


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models", nargs="*", help="only these slugs")
    ap.add_argument("--include-drafts", action="store_true", help="build status: draft models too")
    ap.add_argument("--out", default=str(REPO / "dist"))
    ap.add_argument("--keep-work", action="store_true")
    args = ap.parse_args()

    args.present = have_present()
    args.stories = have_ai_key()
    if not args.present:
        print("WARNING: latris_present not installed — building models but rendering nothing.")
        print("         Install the app's package: pip install -e ../latris-app")

    dist = Path(args.out)
    dist.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="latris-examples-"))

    specs = []
    for d in sorted((REPO / "models").iterdir()):
        if not (d / "model.yaml").exists():
            continue
        m = yaml.safe_load((d / "model.yaml").read_text(encoding="utf-8"))
        if args.models and m["slug"] not in args.models:
            continue
        if m.get("status", "live") == "draft" and not args.include_drafts:
            continue
        specs.append(d)

    entries, failures = [], []
    try:
        for spec_dir in specs:
            slug = spec_dir.name
            try:
                entries.append(build_one(spec_dir, args, dist, work))
            except Exception:  # noqa: BLE001 — one bad model shouldn't hide the rest
                failures.append(slug)
                print(f"[{slug}] FAILED")
                traceback.print_exc()
    finally:
        if not args.keep_work:
            shutil.rmtree(work, ignore_errors=True)
        else:
            print(f"work dir kept: {work}")

    index = {
        "generated_by": "latris-examples tools/build_all.py",
        "models": entries,
    }
    (dist / "gallery.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")

    # The gallery index page: static, renders gallery.json client-side, so
    # every republish picks up new or updated models with no hand edits.
    site_index = REPO / "site" / "index.html"
    if site_index.exists():
        shutil.copy2(site_index, dist / "index.html")

    print(f"\ngallery.json: {len(entries)} model(s)" + (f", {len(failures)} FAILED: {failures}" if failures else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
