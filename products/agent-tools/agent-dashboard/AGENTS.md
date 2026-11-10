# Agent dashboard project

Read the workspace AGENTS.md. This project wraps the pinned Agenttrail Kitchen and Map packages; do not fork its frontend or add another agent orchestrator to change launch behavior.

The launcher starts or reuses a loopback service, checks readiness, and opens a live view. Example mode is scripted and must remain labelled. Observed chefs are responsibilities, not necessarily distinct model sessions. Missing local activity remains unknown.

Keep runtime logs, server registration tokens, PIDs, and dependencies under ignored .runtime/ and node_modules/. Do not print registration tokens, read authentication stores, install provider hooks, or start model agents as a side effect of launching the dashboard. Do not stop an arbitrary process occupying the port.

Run `npm test` for manager logic and verify actual readiness/reuse with `npm run start:headless` and `npm run status`. Use the workspace stop command only for a process the wrapper owns. Existing credentials and provider configurations remain outside this project.

Map uses the same manager with `--map`, separate PID/log/state under `.runtime/map/`
and fixed port 5330. Its version/hash-checked CLI adapter localizes runtime state
and ignores recovery/generated trees; the upstream frontend is unchanged. Never
run upstream init/hooks/autostart merely to open the view. Preserve an existing
PLAN.md; generated ownership has no invented tasks. Verify Map reuse, stop/start
and workspace identity separately from Kitchen.
