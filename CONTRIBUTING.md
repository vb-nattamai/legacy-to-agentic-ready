# Contributing to AgentReady

First off, thank you for considering contributing to **AgentReady**! It's people like you that make this toolkit such a great tool.

## Local Setup

### Clone and Install

```bash
# Clone the repository
git clone https://github.com/vb-nattamai/agent-ready.git
cd agent-ready

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (editable with LLM support)
pip install -e '.[ai,dev]'

# Set up API key for your chosen provider
export ANTHROPIC_API_KEY="sk-ant-..."   # anthropic (default)
export OPENAI_API_KEY="sk-..."           # openai
export GOOGLE_API_KEY="..."              # google
export GROQ_API_KEY="gsk_..."            # groq
export MISTRAL_API_KEY="..."             # mistral
export TOGETHER_API_KEY="..."            # together
# ollama: no key needed — runs locally
```

## Testing the Transformer

### Test on a Sample Repository

```bash
# Clone the bowling-kata (Java/Maven example)
cd /tmp
git clone https://github.com/vb-nattamai/bowling-kata.git

# Run the transformer (dry-run — no files written)
cd bowling-kata
agent-ready --target . --dry-run

# Check what would be generated
ls -la AGENTS.md CLAUDE.md agent-context.json 2>/dev/null || echo "Dry-run: no files written"

# Now generate for real
agent-ready --target .

# Verify output
git diff
```

### Test With a Different Provider

```bash
# Anthropic (default)
export ANTHROPIC_API_KEY="sk-ant-..."
agent-ready --target /path/to/test/repo

# OpenAI
export OPENAI_API_KEY="sk-..."
agent-ready --target /path/to/test/repo --provider openai

# Groq (fast, free tier available)
export GROQ_API_KEY="gsk_..."
agent-ready --target /path/to/test/repo --provider groq

# Local via Ollama (no API key)
agent-ready --target /path/to/test/repo --provider ollama

# Any LiteLLM model string
agent-ready --target /path/to/test/repo --model mistral/mistral-large-latest
```

## Adding a New Generated Artifact

AgentReady v2 uses an LLM-first pipeline — there are no template files to fill. Generation happens by adding a function to `src/agent_ready/generator.py` and wiring it into `LLMGenerator`.

### Step 1: Add a generation function

Add a function to `src/agent_ready/generator.py`. For LLM-generated artifacts, call `_call(model, prompt)`. For deterministic artifacts (like `.cursorrules`), build the content directly from the `analysis` dict.

```python
def generate_my_artifact(model: str, analysis: dict[str, Any]) -> str:
    return _call(
        model,
        f"""\
Generate a <artifact-name> file for this repository.
Repository analysis: {_analysis_block(analysis)}
...
""",
    )
```

### Step 2: Add a private method to `LLMGenerator`

```python
def _my_artifact(self) -> None:
    if not self.quiet:
        print("  ✍️  Generating my-artifact...")
    self._write("my-artifact.md", generate_my_artifact(self.model, self.analysis))
```

### Step 3: Wire into `generate_all()`

Add `self._my_artifact()` in the appropriate position in `LLMGenerator.generate_all()`.

### Step 4: Update `SKIP_AGENT_FILES` or `SKIP_AGENT_DIRS`

In `src/agent_ready/analyser.py`, add the new filename to `SKIP_AGENT_FILES` (or the directory to `SKIP_AGENT_DIRS`) to prevent circular re-ingestion on the next run.

### Step 5: Add tests

Add tests in `tests/test_generator.py` covering the new function and its write integration. The CI gate is `--cov-fail-under=50` — maintain coverage.

## Adding a New Platform-Specific Agent Definition

Model after `.github/agents/agent-ready.agent.md` or `.claude/agents/agent-ready.agent.md`. These are instruction files for specific AI platforms, not generated output — they live in the AgentReady repo itself and describe how to invoke the transformer.

## Running Tests

```bash
# Run the full test suite
pytest

# With coverage report
pytest --cov=src/agent_ready

# Test transformer on live repos (dry-run)
agent-ready --target /path/to/python-repo --dry-run
agent-ready --target /path/to/java-repo --dry-run
agent-ready --target /path/to/ts-repo --dry-run
```

## Pull Request Checklist

Before submitting a PR, ensure:

- [ ] New output filenames added to `SKIP_AGENT_FILES` or `SKIP_AGENT_DIRS` in `analyser.py`
- [ ] New artifacts included in `build_codeowners()` in `generator.py`
- [ ] README.md and `docs/automation.md` updated if new artifact added
- [ ] No hardcoded paths or usernames in code
- [ ] All tests passing (`PYTHONPATH=src pytest -q --cov=src/agent_ready --cov-fail-under=50`)
- [ ] Code linted with `ruff` (`ruff check src/ tests/ && ruff format --check src/ tests/`)

## Code Style

```bash
# Lint and format check
ruff check src/ tests/
ruff format --check src/ tests/

# Auto-fix formatting
ruff format src/ tests/

# Check syntax
python -m py_compile src/agent_ready/cli.py
```

## How Can I Contribute?

### Reporting Bugs

Before creating a bug report, check the issue list. When creating one, include:

* Clear and descriptive title
* Exact steps to reproduce
* Specific examples
* What you observed vs. what you expected
* Your environment (OS, Python version, etc.)

### Suggesting Enhancements

Create an issue with:

* Clear and descriptive title
* Step-by-step description
* Specific examples
* Why this would be useful

### Adding Examples

Add new examples in `docs/EXAMPLES.md`:

```markdown
## Example: {Language + Framework}

**Project:** [Project Name](link)

```bash
# Commands to run transformer
agent-ready --target /path/to/project
```

**Generated files:**
- ✅ AGENTS.md
- ✅ CLAUDE.md
- ... etc
```

## Commit Message Guidelines

Release automation in `.github/workflows/release.yml` parses Conventional Commit prefixes (`feat:`, `fix:`, and `BREAKING CHANGE:`). Commitlint is not currently enforced by CI in this repository.

* Use present tense ("Add feature" not "Added feature")
* Use imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit first line to 72 characters
* Reference issues/PRs liberally after first line

Example:
```
Add Ruby/Rails support to transformer

- Detect .rb files and Gemfile  
- Generate Rails-specific agent instructions
- Add tool.ruby.template.rb scaffold

Fixes #42
```

---

**Thank you for contributing! 🎉**
