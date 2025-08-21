from pathlib import Path

# 모델 파일/폴더 경로 관리 (학습/서빙 공용)
BASE = Path("models")
BASE.mkdir(exist_ok=True, parents=True)


def path(*parts: str) -> Path:
    p = BASE.joinpath(*parts)
    p.parent.mkdir(exist_ok=True, parents=True)
    return p


def exists(*parts: str) -> bool:
    return path(*parts).exists()


def listdir(rel: str = "") -> list[str]:
    p = BASE / rel
    if not p.exists():
        return []
    return [x.name for x in p.iterdir()]
