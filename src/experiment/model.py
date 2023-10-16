from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Literal, Union
from data.model import InstanceMetadata
from polars import DataFrame
import datetime as dt


@dataclass(frozen=True)
class SeriesOutputFiles:
    directory: Path
    event_files: Dict[str, Path]
    run_metadata_file: Path


@dataclass(frozen=True)
class SeriesOutputMetadata:
    solution_string: str
    hash: str
    fitness: int
    generation_count: int
    total_time: int
    chromosome: list[float]


@dataclass(frozen=True)
class SeriesOutputData:
    event_data: Dict[str, DataFrame]
    metadata: SeriesOutputMetadata

    def data_for_event(self, event: str) -> Optional[DataFrame]:
        return self.event_data.get(event, None)


@dataclass
class SeriesOutput:
    data: Optional[SeriesOutputData]
    files: SeriesOutputFiles

    def is_materialized(self) -> bool:
        return self.data is None


@dataclass
class SolverParams:
    input_file: Path
    output_dir: Path


@dataclass
class SolverRunMetadata:
    duration: dt.timedelta
    status: int  # Executing process return code

    def is_ok(self) -> bool:
        """ Whether the computation completed without any errors """
        return self.status == 0


@dataclass
class SolverResult:
    series_output: SeriesOutput
    run_metadata: SolverRunMetadata


@dataclass(frozen=True)
class ExperimentConfig:
    """ Experiment is a series of solver runs over single test case """
    input_file: Path
    output_dir: Path
    n_series: int

    def as_dict(self) -> dict:
        return {
            "input_file": str(self.input_file),
            "output_dir": str(self.output_dir),
            "n_series": self.n_series
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'ExperimentConfig':
        return ExperimentConfig(
            input_file=d['input_file'],
            output_dir=d['output_dir'],
            n_series=d['n_series']
        )


@dataclass
class ExperimentResult:

    """ Each experiment series output is stored in separate directory """
    series_outputs: list[SeriesOutput]

    """ Computations might be repeated > 1 times to average results,
        hence `run_metadata` is a list """
    metadata: Optional[list[SolverRunMetadata]] = None

    def n_series(self) -> int:
        return len(self.series_outputs)

    def has_metadata(self) -> bool:
        return self.metadata is not None


@dataclass
class Experiment:
    """ Instance description, run configuration, result obtained """
    name: str
    instance: InstanceMetadata
    config: ExperimentConfig
    result: Optional[ExperimentResult] = None

    def has_result(self) -> bool:
        return self.result is not None

    def as_dict(self) -> dict:
        # result field is not serialized on purpose
        # it enforces thoughts that result should not be stored in this class
        return {
            "name": self.name,
            "instance": self.instance.as_dict(),
            "config": self.config.as_dict(),
        }

    @classmethod
    def from_dict(cls, exp_dict: dict) -> 'Experiment':
        return cls(name=exp_dict["name"],
                   instance=InstanceMetadata.from_dict(exp_dict["instance"]),
                   config=ExperimentConfig.from_dict(exp_dict["config"]))



