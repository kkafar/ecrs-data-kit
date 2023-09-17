from typing import Dict
from pathlib import Path
from data.model import (
    InstanceMetadata,
)
from experiment.model import (
    ExperimentBundle,
    ExperimentConfig,
    ExperimentResult
)


def create_exp_bundles_from_results(
        results: list[ExperimentResult],
        metadata_store: Dict[str, InstanceMetadata]) -> list[ExperimentBundle]:
    return [
        ExperimentBundle(
            metadata_store.get(result.name),
            result.config,
            result
        )
        for result in results
    ]


def exp_name_from_input_file(input_file: Path) -> str:
    return input_file.stem

def base_output_path_resolver(input_file: Path, output_dir: Path) -> Path:
    return output_dir.joinpath(input_file.stem + '-result').with_suffix('.txt')
