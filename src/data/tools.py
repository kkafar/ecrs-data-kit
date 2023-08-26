import polars as pl
import matplotlib.pyplot as plt
from pathlib import Path
from experiment.model import ExperimentResult, ExperimentDescription
from data.model import Col, Event, EventConfig, config_for_event, EventName
from typing import Iterable, Optional


def data_frame_from_file(data_file: Path) -> pl.DataFrame:
    df = (pl.read_csv(data_file,
                      has_header=False))
    return df


def extract_data_for_event_with_config(data: pl.DataFrame, config: EventConfig) -> pl.DataFrame:
    selected_columns = [data.columns[i] for i in config.raw_columns]
    df = (data
          .filter(pl.col(Col.EVENT) == config.name)
          .select(selected_columns))
    df.columns = config.record_schema
    return df


def partition_experiment_data_by_event(data: pl.DataFrame) -> dict[EventName, pl.DataFrame]:
    return {
        event_name: extract_data_for_event_with_config(data, config_for_event(event_name))
        for event_name in Event.ALL_EVENTS
    }


def join_data_from_multiple_runs(output_files: Iterable[Path]) -> pl.DataFrame:
    main_df: Optional[pl.DataFrame] = None
    for sid, data_file in enumerate(output_files):
        print(f'Processing data file {data_file} sid {sid}')
        tmp_df: pl.DataFrename = data_frame_from_file(data_file)
        series_column = pl.Series("sid", [sid for _ in range(tmp_df.height)])
        tmp_df = tmp_df.with_columns(series_column).rename({'column_1': Col.EVENT})
        if main_df is not None:
            main_df.vstack(tmp_df, in_place=True)
        else:
            main_df = tmp_df
    return main_df


def plot_best_in_gen(data: pl.DataFrame, plot: plt.Axes):
    """ Expects rows in `data` to comply to schema for `Event.BEST_IN_GEN` """
    n_series = data.get_column(Col.SID).n_unique()
    for sid in range(n_series):
        series_data = (
            data
            .lazy()
            .filter(pl.col(Col.SID) == sid)
            .sort(Col.GENERATION)
            .collect()
        )
        print(series_data)
        y_data = series_data.get_column(Col.FITNESS)
        x_data = series_data.get_column(Col.GENERATION)
        plt.plot(x_data, y_data, marker='o', linestyle='--', label=f'Series {sid}')


def plot_diversity(data: pl.DataFrame, plot: plt.Axes):
    """ Expects rows in `data` to comply to schema for `Event.DIVERSITY` """
    series_ids = data.get_column(Col.SID).unique()
    for sid in series_ids:
        series_data = (
            data
            .lazy()
            .filter(pl.col(Col.SID) == sid)
            .sort(Col.GENERATION)
            .collect()
        )
        print(series_data)
        y_data = series_data.get_column(Col.DIVERSITY)
        x_data = series_data.get_column(Col.GENERATION)
        plt.plot(x_data, y_data, marker='o', linestyle='--', label=f'Series {sid}')



def process_experiment_data(data: pl.DataFrame, desc: ExperimentDescription):
    partitioned_data = partition_experiment_data_by_event(data)

    # TODO: Extract these to separate functions

    fig, plot = plt.subplots(nrows=1, ncols=1)
    plot_best_in_gen(partitioned_data.get(Event.BEST_IN_GEN), plot)
    plot.set(
        title=f"Best fitness by generation, {desc.name}",
        xlabel="Generation",
        ylabel="Fitness value"
    )
    plot.legend()
    plt.show()


def process_experiment_results(exp_results: list[ExperimentResult]):
    for result in exp_results:
        print(f'Processing {result.description.name}')
        experiment_data = join_data_from_multiple_runs(result.output_files)
        # print(experiment_data)
        process_experiment_data(experiment_data, result.description)
        # for event_name in Event.ALL_EVENTS:
        #     extract_data_for_event_with_config(
        #         experiment_data, config_for_event(event_name))
        break

