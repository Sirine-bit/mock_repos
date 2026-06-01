# Gold RCA

## Scenario
A frontend build pipeline runs `npm run build` which executes `node scripts/build.js`. The script allocates 5000 in-memory `Buffer` chunks and then concatenates them all at once with `Buffer.concat(bundles)`. The Node V8 heap is exhausted and the process dies with `FATAL ERROR: Ineffective mark-compacts near heap limit Allocation failed - JavaScript heap out of memory`. The build stage fails, deploy is skipped, and the post-action `docker rm` prints noise (`Error: No such container: my_container`) but is not the failure cause.

## Terminal Failure
- Stage: `Build Frontend`
- Correct class: `CODEBASE_ISSUE` (the build script itself is memory-irresponsible)
- Correct RCA Subtype: `RESOURCE_EXHAUSTION` (acceptable: `APPLICATION_EXCEPTION` — the V8 `FATAL ERROR` can be read as the script's own exception)
- Correct Investigator Defect Type: `logic_error` (acceptable: `misconfiguration`)
- Terminal error literal: `FATAL ERROR: Ineffective mark-compacts near heap limit Allocation failed - JavaScript heap out of memory`, followed by `ERROR: npm run build failed with exit code 1`.
- The `docker rm -f my_container ... Error: No such container` line in the post-action is **noise**, NOT the failure cause; the build had already exited 1 before post.

## Root Cause In This Fixture
[scripts/build.js](./scripts/build.js) allocates `5000` `Buffer` objects of ~1024 bytes each, holds them all in the `bundles` array (≈ 5 MB), then calls `Buffer.concat(bundles)` which allocates a single contiguous buffer of equivalent size on top of the originals. In a constrained Node.js process this combined allocation pushes V8 beyond the default heap limit and triggers the OOM. The script's algorithm is a classic "build everything in memory at once" anti-pattern: it should stream / write chunks incrementally instead of materialising the whole bundle.

This is a code defect, not an infrastructure defect. Bumping `--max-old-space-size` would mask the issue (and is a valid operational palliative) but the **real** fix is to refactor `scripts/build.js` to avoid building all bundles at once in memory.

## Defective Location
- Primary file: `scripts/build.js`
- Function: `buildAllAtOnce()` (called by `main()`)
- Defective pattern: `const bundles = Array.from({length: 5000}, ...)` materialising every chunk, plus `Buffer.concat(bundles)` doubling the live-set
- Defect type: `logic_error` (acceptable: `resource_exhaustion` if treated as a memory anti-pattern category)

## Evidence The Agent Should Use
- [scripts/build.js](./scripts/build.js) — the actual memory-heavy implementation pattern. THIS is the smoking gun.
- [Jenkinsfile](./Jenkinsfile) — confirms `npm run build` is the failing step and there is no `--max-old-space-size` override in the pipeline.
- [package.json](./package.json) — confirms `build` resolves to `node scripts/build.js`.
- The Node `FATAL ERROR: Ineffective mark-compacts near heap limit` line in the log — confirms V8 OOM, not external service.

## How The Agent Should Reason
1. Read the log. `FATAL ERROR: ... JavaScript heap out of memory` from V8 → Node process OOM → script-level, not OS-level. The Node process exited before any system OOM-killer was involved.
2. Note that `npm run build` -> `node scripts/build.js`. Inspect `scripts/build.js`.
3. Read `scripts/build.js`. Observe the 5000-chunk allocation in `bundles` and the `Buffer.concat(bundles)` line. Conclude the script materialises the whole bundle in memory.
4. Confirm there is no streaming / chunking. The defect is the algorithm choice in `buildAllAtOnce()`.
5. Recommend a code refactor: stream bundles to disk / pipe to an output stream instead of `Buffer.concat`; OR (palliative) add `node --max-old-space-size=4096 scripts/build.js` in `package.json` / `Jenkinsfile`. Strong answer surfaces BOTH and labels the streaming refactor as the real fix.

## What A Strong Answer Must Say
- Terminal failure is a V8 heap OOM in `node scripts/build.js`; the docker rm post-action noise is unrelated.
- The defect class is `CODEBASE_ISSUE` (`logic_error` / memory pattern in `scripts/build.js`), NOT pure infrastructure.
- The fix targets `scripts/build.js` (`buildAllAtOnce`); a `--max-old-space-size` bump is acceptable as a stopgap but the answer must call it a palliative, not the real fix.
- Investigator MUST inspect `scripts/build.js` (and ideally `package.json` / `Jenkinsfile` for context). It must NOT short-circuit to `SKIPPED_INFRA`.

## What Should Be Marked Wrong
- Classifying as `INFRASTRUCTURE_ISSUE / RESOURCE_EXHAUSTION` and triggering `SKIPPED_INFRA` — the Node heap is a process-level boundary, not an infrastructure one, and the cause lives in the script.
- Recommending only `--max-old-space-size=...` without naming the underlying algorithm defect.
- Treating the docker post-action error as the terminal failure.
- Suggesting the build agent (`build-node-xyz`) is undersized — the agent runs Node fine; the script asks for too much.
- Defect Type values like `null_reference`, `missing_key`, `wrong_type`, `truncation`, `pipeline_wiring_issue`. The defect is `logic_error` (or `resource_exhaustion`-as-code-pattern).
- Investigation Status `SKIPPED_INFRA` — this is codebase-side.
