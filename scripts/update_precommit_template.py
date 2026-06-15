import subprocess
import yaml
import re
from pathlib import Path


TEMPLATE_FILE = Path("template/.pre-commit-config.yaml.jinja")
CONFIG_FILE = Path(".pre-commit-config.yaml")

JINJA_PATTERN = re.compile(r"({{[\s\S]*?}}|{%[\s\S]*?%})")


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def extract_revs(cfg: dict) -> dict[str, str]:
    return {r["repo"]: r["rev"] for r in cfg.get("repos", [])}


def run_autoupdate() -> None:
    subprocess.run(["prek", "autoupdate"], check=True)


def strip_jinja(template_text: str) -> str:
    """
    Replace any Jinja expressions/tags with empty string.
    """
    return JINJA_PATTERN.sub("", template_text)


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
    if not TEMPLATE_FILE.exists():
        raise FileNotFoundError(TEMPLATE_FILE)

    if not CONFIG_FILE.exists():
        raise FileNotFoundError(CONFIG_FILE)

    # preserve original config
    original_config = CONFIG_FILE.read_text()

    try:
        template_text = TEMPLATE_FILE.read_text()

        # 1. strip jinja and write config
        stripped = strip_jinja(template_text)
        CONFIG_FILE.write_text(stripped)

        # 2. run autoupdate
        run_autoupdate()

        # 3. read updated config + extract revs
        cfg = load_yaml(CONFIG_FILE)
        revs = extract_revs(cfg)

        # 4. patch original template
        updated_template = patch_template(template_text, revs)

        if updated_template != template_text:
            TEMPLATE_FILE.write_text(updated_template)
            print("pre-commit template updated")
            return 1

        print("pre-commit template up to date")
        return 0

    finally:
        # always restore original config
        CONFIG_FILE.write_text(original_config)


if __name__ == "__main__":
    raise SystemExit(main())
