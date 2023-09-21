from .solver import SolverProxy, SolverParams, SolverRunMetadata
from .model import ExperimentResult, ExperimentConfig
from pathlib import Path
from typing import Optional


def base_output_path_resolver(input_file: Path, output_dir: Path, series_id: Optional[int] = None) -> Path:
    file_name = input_file.stem + \
        '-result' + \
        ('-run-' + str(series_id)) if series_id is not None else ''
    return output_dir.joinpath(file_name).with_suffix('.txt')


class ExperimentBatchRunner:
    def __init__(self, solver: SolverProxy, configs: list[ExperimentConfig]):
        self.solver: SolverProxy = solver
        self.configs: list[ExperimentConfig] = configs
        self.runner: ExperimentRunner = ExperimentRunner(self.solver)

    def run(self) -> list[ExperimentResult]:
        # return [self.runner.run(desc) for desc in self.configs]
        return self.runner.run_many(self.configs)


class ExperimentRunner:
    def __init__(self, solver: SolverProxy):
        self.solver: SolverProxy = solver

    def run(self, config: ExperimentConfig) -> ExperimentResult:
        run_metadata: list[SolverRunMetadata] = []
        output_files: list[Path] = []
        for sid in range(1, config.repeats_no + 1):
            out_file = base_output_path_resolver(config.input_file, config.output_dir, sid)
            params = SolverParams(config.input_file, out_file)
            metadata = self.solver.run(params)
            output_files.append(out_file)
            run_metadata.append(metadata)
        return ExperimentResult(output_files, run_metadata)

    def run_many(self, configs: list[ExperimentConfig]) -> list[ExperimentResult]:
        params = []
        for cfg in configs:
            for sid in range(1, cfg.repeats_no + 1):
                out_file = base_output_path_resolver(cfg.input_file, cfg.output_dir, sid)
                params.append(SolverParams(cfg.input_file, out_file))
        
        mds = self.solver.run_many(params)
        return mds

