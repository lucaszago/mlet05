"""Configuration models for the finance project."""

import yaml
from pydantic import BaseModel, ConfigDict, Field


class LSTMParameters(BaseModel):
    """Typed LSTM and dataset parameters loaded from the YAML config."""

    model_config = ConfigDict(populate_by_name=True)

    sequence_length: int = Field(alias="SEQUENCE_LENGTH")
    train_ratio: float = Field(alias="TRAIN_RATIO")
    epochs: int = Field(alias="EPOCHS")
    batch_size: int = Field(alias="BATCH_SIZE")
    symbol: str = Field(default="DIS", alias="SYMBOL")
    start_date: str = Field(default="2018-01-01", alias="START_DATE")
    end_date: str = Field(default="2024-07-20", alias="END_DATE")


class ProjectConfig(BaseModel):
    """Represent finance project configuration parameters loaded from YAML.

    Handles feature specifications, catalog details, experiment parameters,
    and LSTM settings derived from the training notebook.
    Supports environment-specific configuration overrides.
    """

    num_features: list[str]
    cat_features: list[str]
    target: str
    catalog_name: str
    schema_name: str
    pipeline_id: str
    experiment_name_basic: str
    experiment_name_custom: str
    experiment_name_fe: str
    parameters: LSTMParameters

    @classmethod
    def from_yaml(cls, config_path: str, env: str = "dev") -> "ProjectConfig":
        """Load and parse configuration settings from a YAML file.

        :param config_path: Path to the YAML configuration file
        :param env: Environment name to load environment-specific settings
        :return: ProjectConfig instance initialized with parsed configuration
        """
        if env not in ["prd", "acc", "dev"]:
            raise ValueError(f"Invalid environment: {env}. Expected 'prd', 'acc', or 'dev'")

        with open(config_path) as f:
            config_dict = yaml.safe_load(f)
            config_dict["catalog_name"] = config_dict[env]["catalog_name"]
            config_dict["schema_name"] = config_dict[env]["schema_name"]
            config_dict["pipeline_id"] = config_dict[env]["pipeline_id"]

            return cls(**config_dict)


class Tags(BaseModel):
    """Represents a set of tags for a Git commit.

    Contains information about the Git SHA, branch, and job run ID.
    """

    git_sha: str
    branch: str
    job_run_id: str
