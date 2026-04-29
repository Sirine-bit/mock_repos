const bundles = Array.from({ length: 5000 }, (_, index) =>
  Buffer.from(`chunk-${index}-` + "x".repeat(1024))
);

function buildAllAtOnce() {
  return Buffer.concat(bundles);
}

function main() {
  console.log("Compiling assets...");
  console.log("Processing CSS...");
  console.log("Building bundles...");
  buildAllAtOnce();
}

main();
