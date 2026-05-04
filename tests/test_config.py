"""Tests for project configuration loading."""

from pathlib import Path

from finance.config import ProjectConfig


def test_config_loads_dev_environment() -> None:
    config = ProjectConfig.from_yaml(str(Path("project_config.yml")), env="dev")

    assert config.catalog_name == "mlops_dev"
    assert config.schema_name == "finance"
    assert config.parameters.symbol == "DIS"
