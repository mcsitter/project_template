import subprocess
import yaml
from pathlib import Path


TEMPLATE_FILE = Path("template/.pre-commit-config.yaml.jinja")
CONFIG_FILE = Path(".pre-commit-config.yaml")


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def extract_revs(cfg: dict) -> dict[str, str]:
    return {r["repo"]: r["rev"] for r in cfg.get("repos", [])}


def run_autoupdate() -> None:
    subprocess.run(["prek", "autoupdate"], check=True)


def patch_template(template_text: str, revs: dict[str, str]) -> str:
    out = []
    current_repo = None

    for line in template_text.splitlines():
        stripped = line.strip()

        if stripped.startswith("- repo:"):
            current_repo = stripped.split("repo:", 1)[1].strip()

        if current_repo and stripped.startswith("rev:"):
            if current_repo in revs:
                indent = line[: line.index("rev:")]
                line = f"{indent}rev: {revs[current_repo]}"

        out.append(line)

    return "\n".join(out) + "\n"


def main() -> int:
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(CONFIG_FILE)

    run_autoupdate()

    cfg = load_yaml(CONFIG_FILE)
    revs = extract_revs(cfg)

    if not TEMPLATE_FILE.exists():
        raise FileNotFoundError(TEMPLATE_FILE)

    original = TEMPLATE_FILE.read_text()
    updated = patch_template(original, revs)

    if original != updated:
        TEMPLATE_FILE.write_text(updated)
        print("pre-commit template updated")
        return 1

    print("pre-commit template up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
