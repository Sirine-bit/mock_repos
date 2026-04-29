# Gold RCA

## Scenario
The log shows a frontend build that ends with a Node heap OOM, followed by a noisy post-action container cleanup error.

## Terminal Failure
- Stage: `Build Frontend`
- Correct class: `CODEBASE_ISSUE` or resource-heavy build design causing OOM
- Important nuance: the later `docker rm` error is a post-failure cascade and should not be selected as the root cause

## Root Cause In This Fixture
The build script [scripts/build.js](./scripts/build.js) allocates a very large in-memory bundle set and concatenates everything at once with `Buffer.concat(bundles)`. This all-at-once strategy is the repo-local behavior most consistent with the logged Node heap exhaustion during `npm run build`.

## Defective Location
- File: `scripts/build.js`
- Function/block: `buildAllAtOnce`
- Defect type: `logic_error` / memory-inefficient build implementation

## Evidence The Agent Should Use
- [package.json](./package.json) shows `npm run build` executes `node scripts/build.js`.
- [scripts/build.js](./scripts/build.js) shows the aggressive memory allocation pattern.
- [Jenkinsfile](./Jenkinsfile) confirms the build stage precedes the post-action cleanup noise.

## How The Agent Should Reason
1. Ignore the post-action `docker rm` failure because it occurs after the build already failed.
2. Start from the build command and resolve the script from `package.json`.
3. Inspect `scripts/build.js` and confirm it performs memory-heavy all-at-once concatenation.
4. Attribute the terminal failure to the build implementation pattern that drives heap pressure.

## What A Strong Answer Must Say
- The root cause is in the frontend build step, not the post-action cleanup.
- The relevant file is `scripts/build.js`.
- The problematic behavior is bulk in-memory concatenation of bundles.

## What Should Be Marked Wrong
- Choosing `docker rm -f my_container` as the terminal failure.
- Calling the repo defect “missing Jenkinsfile”.
- Giving a generic OOM diagnosis without tying it to `scripts/build.js`.
