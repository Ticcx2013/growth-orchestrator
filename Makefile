.PHONY: setup run demo test eval eval-live record open clean

UV := $(shell command -v uv 2>/dev/null || echo $(HOME)/.local/bin/uv)

setup:            ## Install uv (if missing) and all dependencies
	@command -v uv >/dev/null 2>&1 || curl -LsSf https://astral.sh/uv/install.sh | sh
	$(UV) sync
	@echo "\nReady. Run 'make run' and open http://localhost:8000"

run:              ## Start the API + console on http://localhost:8000
	$(UV) run uvicorn growth_orchestrator.api:app --host 127.0.0.1 --port 8000 --reload --app-dir src

demo:             ## Narrated CLI demo of all scenarios (offline if no ANTHROPIC_API_KEY)
	$(UV) run python demo/run_demo.py

test:             ## Automated tests for the critical business logic
	$(UV) run pytest -q

eval:             ## AI evaluation suite (offline uses recorded responses)
	$(UV) run python evals/run_eval.py

eval-live:        ## AI evaluation suite against the live API (needs ANTHROPIC_API_KEY)
	GO_AI_MODE=live $(UV) run python evals/run_eval.py --label $${GO_MODEL:-claude-opus-5-5}

record:           ## Live run that also records model responses as offline fixtures
	GO_AI_MODE=record $(UV) run python evals/run_eval.py --label $${GO_MODEL:-claude-opus-5-5}
	GO_AI_MODE=record $(UV) run python demo/run_demo.py > /dev/null

clean:
	rm -rf data/*.db data/*.db-* .pytest_cache
