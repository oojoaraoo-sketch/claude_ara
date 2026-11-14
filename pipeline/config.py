import os
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PUBLIC_DIR = ROOT / "public"
DB_PATH = DATA_DIR / "pipeline.db"


def load_config(path: Path | None = None) -> dict:
    with open(path or ROOT / "config.toml", "rb") as f:
        cfg = tomllib.load(f)
    # 환경변수로 덮어쓰기 (GitHub Actions에서 사이트 주소 등을 바꿀 때)
    if os.environ.get("SITE_BASE_URL"):
        cfg["site"]["base_url"] = os.environ["SITE_BASE_URL"]
    if os.environ.get("PIPELINE_ENABLED", "").lower() == "false":
        cfg["safety"]["enabled"] = False
    cfg["site"]["base_url"] = cfg["site"]["base_url"].rstrip("/")
    return cfg
