import polars as pl
import matplotlib.pyplot as plt
import core.fs
import core.conversion
import json
from typing import Dict, Optional
from pathlib import Path
from experiment.model import (
    ExperimentResult,
    Experiment,
)
from data.model import (
    Col,
    Event,
    InstanceMetadata,
    JoinedExperimentData,
)
from .plot import (
    plot_diversity,
    plot_best_in_gen,
    plot_best_in_gen_agg,
)
from core.series import load_series_output, materialize_series_output


def experiment_result_from_dir(directory: Path, materialize: bool = False) -> ExperimentResult:
    # Metadata collected by SolverProxy is not dumped on the disk currently.
    # TODO: dump it on the disk & load it here
    result = ExperimentResult([], None)
    for series_dir in filter(lambda file: file.is_dir(), directory.iterdir()):
        series_output = load_series_output(series_dir, lazy=materialize)
        result.series_outputs.append(series_output)

    return result


def extract_experiment_results_from_dir(directory: Path, materialize: bool = False) -> list[ExperimentResult]:
    exp_results = []
    for exp_dir in filter(lambda file: file.is_dir(), directory.iterdir()):
        exp_results.append(experiment_result_from_dir(exp_dir, materialize))
    return exp_results


def experiment_from_dir(directory: Path, materialize: bool = False) -> Experiment:
    exp_file = core.fs.experiment_file_from_directory(directory)
    exp: Experiment = None
    with open(exp_file, 'r') as file:
        exp = json.load(file, object_hook=core.conversion.deserialize_experiment_from_dict)

    assert exp is not None, f"Failed to load experiment configuration data for {exp_file}"

    exp_result = experiment_result_from_dir(directory, materialize)
    exp.result = exp_result
    return exp


def extract_experiments_from_dir(directory: Path) -> list[Experiment]:
    return [
        experiment_from_dir(d) for d in filter(lambda f: f.is_dir(), directory.iterdir())
    ]


def data_frame_from_file(data_file: Path, has_header: bool = False) -> pl.DataFrame:
    df = (pl.read_csv(data_file,
                      has_header=has_header))
    return df


def _update_df_with(base_df: pl.DataFrame, new_df: pl.DataFrame) -> pl.DataFrame:
    if base_df is not None:
        base_df.vstack(new_df, in_place=True)
    else:
        base_df = new_df
    return base_df


def _add_sid_column_to_df(df: pl.DataFrame, sid: int) -> pl.DataFrame:
    return df.with_columns(pl.Series(Col.SID, [sid for _ in range(0, df.shape[0])]))


def experiment_data_from_all_series(experiment: Experiment) -> JoinedExperimentData:
    exp_data = JoinedExperimentData(
        newbest=None,
        diversity=None,
        bestingen=None,
        popgentime=None,
        iterinfo=None
    )

    for sid, series_output in enumerate(experiment.result.series_outputs):
        if not series_output.is_materialized():
            materialize_series_output(series_output, force=False)

        exp_data.newbest = _update_df_with(exp_data.newbest, _add_sid_column_to_df(series_output.data.data_for_event(Event.NEW_BEST), sid))
        exp_data.diversity = _update_df_with(exp_data.diversity, _add_sid_column_to_df(series_output.data.data_for_event(Event.DIVERSITY), sid))
        exp_data.bestingen = _update_df_with(exp_data.bestingen, _add_sid_column_to_df(series_output.data.data_for_event(Event.BEST_IN_GEN), sid))
        exp_data.popgentime = _update_df_with(exp_data.popgentime, _add_sid_column_to_df(series_output.data.data_for_event(Event.POP_GEN_TIME), sid))
        exp_data.iterinfo = _update_df_with(exp_data.iterinfo, _add_sid_column_to_df(series_output.data.data_for_event(Event.ITER_INFO), sid))

    return exp_data


def process_experiment_data(exp: Experiment, data: JoinedExperimentData):
    print(f"Processing experiment {exp.name}")
    #
    # fig, plot = plt.subplots(nrows=1, ncols=1)
    # plot_best_in_gen(plot, data.bestingen, exp.instance)
    # plot.set(
    #     title=f"Best fitness by generation, {exp.name}",
    #     xlabel="Generation",
    #     ylabel="Fitness value"
    # )
    # plot.legend()
    #
    # fig, plot = plt.subplots(nrows=1, ncols=1)
    # plot_diversity(plot, data.diversity, exp.instance)
    # plot.set(
    #     title=f"Diversity rate by generation, {exp.name}",
    #     xlabel="Generation",
    #     ylabel="Diversity rate"
    # )
    # plot.legend()

    fig, plot = plt.subplots(nrows=1, ncols=1)
    plot_best_in_gen_agg(plot, data.bestingen, exp.instance)
    plot.set(
        title=f"Average best fitness by generation, {exp.name}",
        xlabel="Generation",
        ylabel="Average best fitness"
    )
    plot.legend()

    plt.show()


def process_experiment_batch_output(batch: list[Experiment]):
    for exp in batch:
        exp_data: JoinedExperimentData = experiment_data_from_all_series(exp)
        process_experiment_data(exp, exp_data)


def maybe_load_instance_metadata(metadata_file: Optional[Path]) -> Optional[Dict[str, InstanceMetadata]]:
    if metadata_file is None:
        return None
    df: pl.DataFrame = data_frame_from_file(metadata_file, has_header=True)
    metadata_store = {}
    for record in df.iter_rows():
        metadata = InstanceMetadata(*record)
        metadata_store[metadata.id] = metadata
    return metadata_store

