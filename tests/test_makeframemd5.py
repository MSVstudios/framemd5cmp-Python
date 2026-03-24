import pytest
from pathlib import Path
from makeframemd5 import build_options, parse_args

@pytest.fixture(autouse=True)
def setup_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path

def test_build_options_default(tmp_path):
    input_path = tmp_path / "sample.mp4"
    input_path.write_text("dummy", encoding="utf-8")
    output_dir = tmp_path / "framemd5"
    
    # Mocking Namespace object evitando accoppiamento con stringhe di path Windows/Linux
    class Args:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    
    args = Args(input=str(input_path), d=False, c=False, f=False, force=False, version=False)
    
    requests = build_options(input_path, output_dir, args)

    assert len(requests) == 1
    # Confronto tra Path objects per gestire separatori / e \
    expected_path = output_dir / "sample_framemd5.md5"
    assert Path(requests[0][-1]) == expected_path

def test_build_options_flags(tmp_path):
    input_path = tmp_path / "source.mp4"
    input_path.write_text("dummy", encoding="utf-8")
    output_dir = tmp_path / "framemd5"

    class Args:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    args = Args(input=str(input_path), d=True, c=True, f=True, force=False, version=False)
    requests = build_options(input_path, output_dir, args)

    assert len(requests) == 3
    names = {Path(r[-1]).name for r in requests}
    expected_names = {
        "source_framemd5.md5",
        "source_codec_copy_framemd5.md5",
        "source_monow_sqcif_framemd5.md5"
    }
    assert expected_names.issubset(names)

def test_build_options_force(tmp_path):
    input_path = tmp_path / "example.mp4"
    input_path.write_text("dummy", encoding="utf-8")
    output_dir = tmp_path / "framemd5"
    output_dir.mkdir(parents=True, exist_ok=True)

    existing = output_dir / "example_framemd5.md5"
    existing.write_text("old", encoding="utf-8")

    class Args:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    args = Args(input=str(input_path), d=False, c=False, f=False, force=True, version=False)
    requests = build_options(input_path, output_dir, args)

    assert len(requests) == 1
    assert Path(requests[0][-1]).name == "example_framemd5.md5"
    # Se build_options gestisce il force eliminando il file:
    assert not existing.exists() or existing.read_text(encoding="utf-8") == ""