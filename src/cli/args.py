from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable


@dataclass
class Args:
    cmd_name: str
    handler: Callable


@dataclass
class RunCmdArgs(Args):
    bin: Path
    input_files: Optional[list[Path]]
    input_dirs: Optional[list[Path]]
    output_file: Optional[Path]
    output_dir: Optional[Path]
    runs: Optional[int]


@dataclass
class AnalyzeCmdArgs(Args):
    names: list[str]