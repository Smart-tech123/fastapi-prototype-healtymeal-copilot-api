from pathlib import Path


class Config:
    ROOT_DIR: Path = Path(__file__).parent.parent.parent.parent
    TEMPLATE_DIR: Path = ROOT_DIR / "app" / "prompts" / "templates"


config = Config()
