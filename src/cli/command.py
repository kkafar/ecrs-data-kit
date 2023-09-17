from .args import RunCmdArgs, AnalyzeCmdArgs
from experiment.runner import ExperimentBatchRunner, ExperimentBatchConfig
from experiment.solver import SolverProxy
from experiment.model import ExperimentResult
from data.file_resolver import resolve_all_input_files
from data.tools import (
    process_experiment_results,
    extract_experiment_results_from_dir,
    maybe_load_instance_metadata
)


def handle_cmd_run(args: RunCmdArgs):
    print(f"RunCommand run with args: {args}")
    # metadata_store = maybe_load_instance_metadata(args.metadata_file)
    runner = ExperimentBatchRunner(
        SolverProxy(args.bin),
        ExperimentBatchConfig(resolve_all_input_files(args.input_files, args.input_dirs),
                              args.output_file, args.output_dir,
                              repeats_no=args.runs if args.runs is not None else 1))

    exp_results: list[ExperimentResult] = runner.run()
    # print(metadata_store)
    process_experiment_results(exp_results)


def handle_cmd_analyze(args: AnalyzeCmdArgs):
    print(f"AnalyzeCommand run with args: {args}")

    exp_results: list[ExperimentResult] = extract_experiment_results_from_dir(args.dir)
    process_experiment_results(exp_results)

