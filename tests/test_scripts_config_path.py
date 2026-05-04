"""Tests for Databricks script config path resolution."""

import importlib.util
from pathlib import Path


def load_script_module(script_name: str):
    script_path = Path("scripts") / script_name
    spec = importlib.util.spec_from_file_location(script_name.replace(".", "_"), script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_process_data_prefers_bundle_files_root(tmp_path) -> None:
    module = load_script_module("process_data.py")
    config_path = tmp_path / "files" / "project_config.yml"
    config_path.parent.mkdir()
    config_path.write_text("x: y")

    assert module.resolve_config_path(str(tmp_path)) == config_path


def test_train_script_falls_back_to_local_project_config() -> None:
    module = load_script_module("02.train_register_fe_model.py")

    assert module.resolve_config_path().name == "project_config.yml"
