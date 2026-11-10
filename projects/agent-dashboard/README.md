# Agenttrail workspace views

This project is an optional local activity monitor for coding work. It installs pinned Agenttrail Map (`0.2.0`) and Kitchen (`0.1.0-alpha.3`) dependencies together. It replaces the fragile launch path inside an older chat's temporary npm cache. The experimental Kitchen visualises local coding activity with chefs, order tickets, and deliverables.

## One click

From the workspace root, double-click **Open-Agent-Dashboard.command** in Finder. It starts or reuses the service, waits for a valid Kitchen response, then opens the selected workspace in live mode at http://127.0.0.1:4780/.

In VS Code, click the play icon beside the root npm script `agents:dashboard`, or run **Agent flows: Open** from Terminal → Run Task. A new checkout's first launch installs the pinned package with lifecycle scripts disabled. Once installed, normal launches use the local project dependency and require no npm download.

The server runs independently of the launching terminal. Double-click **Stop-Agent-Dashboard.command** or use `npm run agents:stop` to stop only the process owned by this launcher. An unrelated service occupying port 4780 is left unchanged, with an actionable error. The service does not silently move to another port.

## Live versus example

Live shows available metadata from the configured workspace folders. If agents are idle or their native logs are unavailable, task progress can be unknown. Chefs represent responsibilities and are not a count of independent agents. This dashboard observes work; it does not start or manage model agents.

For an immediate scripted walkthrough, double-click **Open-Agent-Example.command** or run `npm run agents:example`. The Kitchen labels this as an example. Switch back to Live to observe real work. Missing native metadata must never be presented as a completed task or fabricated handoff.

The pinned version documents experimental local Codex/Claude log observation and optional Claude/Cursor hooks. Kilo, OpenCode, Pi, remote sessions, and VPS schedules are not claimed to have native task adapters here. File activity may still be visible. No provider hooks were installed during this integration.

## Project selection

The workspace project registry is `../../workspace.projects.json`. `dashboard.config.json` selects five project IDs: the workspace root, Playwright Agent, role-aware UI automation, microservices, and the Kafka lab. Retired projects are not watched. Select a project inside the Kitchen to focus its observations. Stop and restart after changing the configured watched set. Up to twelve folders are supported by the pinned release.

## Map versus Kitchen

Use `npm run agents:map` from the workspace root, or double-click
**Open-Agent-Map.command**, to open Map at http://127.0.0.1:5330/. Its managed
launcher verifies workspace identity and reuses the running process. Use
`npm run agents:map:status` / `npm run agents:map:stop`, or **Stop-Agent-Map.command**,
for status and shutdown. VS Code tasks include **Agent map: Open** and **Agent map: Stop**.
Kitchen retains `npm run agents:dashboard` at port 4780.

`npx agenttrail` is the direct upstream Map command; `npx agenttrail-kitchen .`
is the direct Kitchen command. Ordinary workspace launches use the installed,
locked dependencies. Both are observers; coding agents continue running in their
existing tools. Map's task/tool run cards require supported hook events, while
file activity works without hooks. No provider hooks or login autostart were installed.

Map reads the workspace `PLAN.md` when present. The starter maps the nine registered
project roots and includes only the real Map installation tasks. No progress is
invented for other products. The pinned release requires at least two declared
tasks to show its component diagram; otherwise it shows file activity. Without a
user plan, the launcher can generate ownership metadata from the registry inside
its runtime folder; this alone does not invent tasks.

The upstream CLI has no local state-directory option. `scripts/map-adapter.mjs`
checks the exact published 0.2.0 source SHA-256, then prepares a runtime copy with
local persistence under `.runtime/map/state/`, an explicit plan path, a service
identity, recovery/runtime directory exclusions and no alternate-port fallback.
Its upstream frontend and installed package remain unchanged. Updates fail closed
until that small adapter is reviewed. Logs, PID state and generated adapter files
stay under `.runtime/map/`; no HOME override or global Agenttrail cache is used.

## Terminal controls

```sh
npm start
npm run start:headless
npm run example
npm run status
npm run stop
npm test
```

Run these inside this project. Root aliases begin with `agents:`. Source lives in `scripts/`; generated state, registration credentials, PID records, and logs stay in the ignored `.runtime/` folder. `dashboard.log` records startup failures. Do not commit or share the registration files.

If a crash leaves `launch.lock`, confirm no launch is in progress before removing it. No service is registered to start automatically at login. No additional model calls or paid provider setup are introduced by this wrapper.

## Related dashboard

The earlier schedules/Telegram monitor was a separate service on port 4781 under the older chat's outputs. This launcher starts only the requested Kitchen at 4780. It does not contact the VPS or inspect Telegram receipts as a side effect.

Upstream: https://github.com/sodiumsun/agenttrail · pinned package `agenttrail-kitchen@0.1.0-alpha.3` · MIT. Upstream licenses and third-party notices ship with the installed package.
