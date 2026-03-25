## 🤖 Agent Context Drift Detected

The scheduled context refresh found that `agent-context.json` no longer matches the current state of the repository.

This can happen when:
- New modules, services, or packages were added
- Entry points or build commands changed
- New environment variables were introduced

### What changed
See the diff in this PR for the exact changes.

### Before merging
- [ ] Verify `domain_concepts` still reflects real terms from the codebase
- [ ] Verify `restricted_write_paths` is still accurate
- [ ] Verify `environment_variables` covers all new vars introduced since last scan
