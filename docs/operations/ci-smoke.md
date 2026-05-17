# CI smoke test for research_topic

Setup:
1. In repo Settings → Environments → create `smoke-test`
2. Add secret `SMOKE_ANTHROPIC_API_KEY` with a key that has Haiku access
3. Smoke test fires on PRs that touch `tools/research_topic.py` or `sampling/**`
4. Cost cap: ~$0.01 per PR (Haiku is ~$0.25/M input + $1.25/M output)
