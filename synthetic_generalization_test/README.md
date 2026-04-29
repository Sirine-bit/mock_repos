# synthetic_generalization_test

Frontend build fixture for a memory-hungry Node build.

The build script aggressively concatenates every generated bundle into one giant
buffer, which is the kind of pattern that can push a constrained Jenkins node
into a heap OOM during `npm run build`.
