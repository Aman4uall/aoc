from __future__ import annotations

import argparse

from aoc.config import load_project_config
from aoc.pipeline import PipelineRunner


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aoc")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a project from a YAML config.")
    run_parser.add_argument("--config", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect run state for a project.")
    inspect_parser.add_argument("project_id")
    inspect_parser.add_argument("--output-root", default="outputs")

    approve_parser = subparsers.add_parser("approve", help="Approve a named gate for a project.")
    approve_parser.add_argument("project_id")
    approve_parser.add_argument("--gate", required=True)
    approve_parser.add_argument("--note", default="")
    approve_parser.add_argument("--output-root", default="outputs")

    resume_parser = subparsers.add_parser("resume", help="Resume a previously started project.")
    resume_parser.add_argument("project_id")
    resume_parser.add_argument("--output-root", default="outputs")

    render_parser = subparsers.add_parser("render", help="Render the final approved PDF report.")
    render_parser.add_argument("project_id")
    render_parser.add_argument("--output-root", default="outputs")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        config = load_project_config(args.config)
        runner = PipelineRunner(config)
        state = runner.run()
        print(runner.inspect())
        return 0 if state.run_status.value != "blocked" else 1
    if args.command == "inspect":
        runner = PipelineRunner.from_project_id(args.project_id, output_root=args.output_root)
        print(runner.inspect())
        return 0
    if args.command == "approve":
        runner = PipelineRunner.from_project_id(args.project_id, output_root=args.output_root)
        runner.approve_gate(args.gate, notes=args.note)
        print(runner.inspect())
        return 0
    if args.command == "resume":
        runner = PipelineRunner.from_project_id(args.project_id, output_root=args.output_root)
        state = runner.run()
        print(runner.inspect())
        return 0 if state.run_status.value != "blocked" else 1
    if args.command == "render":
        runner = PipelineRunner.from_project_id(args.project_id, output_root=args.output_root)
        path = runner.render()
        print(path)
        return 0
    parser.error(f"Unsupported command {args.command}")
    return 2
