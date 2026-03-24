import shutil
import subprocess
from pathlib import Path
from unittest import mock

import pytest

from framemd5cmp import find_dependency, is_video_file


def test_find_dependency_missing(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _name: None)
    assert find_dependency("ffmpeg") is None


def test_is_video_file_true(monkeypatch, tmp_path):
    p = tmp_path / "a.mp4"
    p.write_text("x")

    fake_result = mock.Mock()
    fake_result.returncode = 0
    fake_result.stdout = "index=0\n"

    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: fake_result)
    assert is_video_file(p)


def test_is_video_file_false(monkeypatch, tmp_path):
    p = tmp_path / "a.mp4"
    p.write_text("x")

    fake_result = mock.Mock()
    fake_result.returncode = 0
    fake_result.stdout = ""

    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: fake_result)
    assert not is_video_file(p)


def test_is_video_file_ffprobe_error(monkeypatch, tmp_path):
    p = tmp_path / "a.mp4"
    p.write_text("x")

    fake_result = mock.Mock()
    fake_result.returncode = 1
    fake_result.stdout = ""

    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: fake_result)
    assert not is_video_file(p)
