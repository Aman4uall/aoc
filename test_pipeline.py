from aoc.config import load_project_config
from aoc.pipeline import PipelineRunner


def main() -> None:
    config = load_project_config("examples/ethylene_glycol_india_mock.yaml")
    config.project_id = "eg-india-demo-decision"
    runner = PipelineRunner(config)
    state = runner.run()
    print(runner.inspect())
    while state.awaiting_gate_id:
        runner.approve_gate(state.awaiting_gate_id, notes="auto-approved for example run")
        state = runner.run()
        print(runner.inspect())
    pdf_path = runner.render()
    print(f"Rendered PDF: {pdf_path}")


if __name__ == "__main__":
    main()
