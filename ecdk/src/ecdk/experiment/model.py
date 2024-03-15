from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict
from data.model import InstanceMetadata
from polars import DataFrame
import datetime as dt


@dataclass(frozen=True)
class SeriesOutputFiles:
    """ Describes structure of output directory for given **series** of given experiment """

    # Path to the series output directory
    directory: Path

    # Mapping of csv event files (see docs on model for format explanation). EventName -> Path
    event_files: Dict[str, Path]

    # Path to the summary of solver output. This file is in JSON format & contains
    # information defined by the `SeriesOutputMetadata` type
    run_metadata_file: Path

    # Stdout file of solver process for given series. Logs, errors, warnings of the solver
    logfile: Optional[Path]


@dataclass(frozen=True)
class SeriesOutputMetadata:
    """ Solver produces file (right now named `run_metadata.json`) with summary information about
    results of single run (single series). This structure models content of this file """

    solution_string: str
    hash: str
    fitness: int
    generation_count: int
    total_time: int
    chromosome: list[float]


@dataclass(frozen=True)
class SeriesOutputData:
    """ In-memory representation of solver output for single run (series output). Holds event information
    in polars DataFrames & additional "metadata" (no idea why I've named it this way) with direct solver result.
    """

    # Mapping EventName -> DataFrame. Each event has a bit different schema. See docs for reference.
    event_data: Dict[str, DataFrame]
    metadata: SeriesOutputMetadata

    def data_for_event(self, event: str) -> Optional[DataFrame]:
        return self.event_data.get(event, None)


@dataclass
class SeriesOutput:
    """ A bit weird type, that holds both the reference (paths of files with single series output data) and if materialized
    (see `is_materialized` method), also holds the data loaded to memory. """

    data: Optional[SeriesOutputData]
    files: SeriesOutputFiles

    def is_materialized(self) -> bool:
        return self.data is not None


@dataclass
class SolverParams:
    """ Models CLI parameters of solver binary. These together with `SolverProxy` instance can be turned into solver invocation.
    TODO: This could be placed somewhere near the solver. I should move away from placing types definition in typescript .d files fashion."""
    input_file: Optional[Path]
    output_dir: Optional[Path]
    config_file: Optional[Path]
    stdout_file: Optional[Path]


@dataclass
class SolverRunMetadata:
    """ Data collected by the runtime process (scheduler) on single solver proces (used for solving single series).
    This is used only in by the "Local" solver, that keeps the runtime process alive for the time of scheduling - this is not used
    in case of HyperQueue.
    """

    duration: dt.timedelta
    status: int  # Executing process return code

    def is_ok(self) -> bool:
        """ Whether the computation completed without any errors """
        return self.status == 0


@dataclass
class SolverResult:
    """ Aggregate type holding both: actual solver single series output and some metadata collected by the scheduler.
    Similarly to `SolverRunMetadata` this is used only in case of "local" solver (for the same reasons).
    """
    series_output: SeriesOutput
    run_metadata: SolverRunMetadata


@dataclass(frozen=True)
class ExperimentConfig:
    """ Experiment is a series of solver runs over single test case. """

    # Path to file with JSSP instance specification
    input_file: Path

    # Path to directory, where subdirectories for given series outputs will be created
    output_dir: Path

    # Optional path to solver config file, this should be passed throught directly to solver
    config_file: Optional[Path]

    # Number of repetitions to run for this experiment
    n_series: int

    def as_dict(self) -> dict:
        return {
            "input_file": str(self.input_file),
            "output_dir": str(self.output_dir),
            "n_series": self.n_series,
            "config_file": str(self.config_file),
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'ExperimentConfig':
        return ExperimentConfig(
            input_file=Path(d['input_file']),
            output_dir=Path(d['output_dir']),
            config_file=Path(d.get('config_file')),
            n_series=d['n_series'],
        )


@dataclass
class ExperimentResult:
    """ Results of all the series of given experiment & optional associated metadata collected by the scheduler.
    Metadata is present only in case of "local" solver (for the same reasons as for many of the types above). """

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
    config: ExperimentConfig  # TODO: Flatten the structure and pass whole Experiment around
    result: Optional[ExperimentResult] = None

    # Directory of the batch this experiment belongs to. Usually the file hierarchy would be
    # batch_dir/config.output_dir.
    batch_dir: Optional[Path] = None  # TODO: Make this not optional

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
                   instance=exp_dict["instance"],
                   config=exp_dict["config"])


@dataclass
class ExperimentBatch:
    """  """

    # Output directory of whole experiment batch (list of experiments)
    output_dir: Path

    # List of experiments to conduct
    experiments: list[Experiment]

