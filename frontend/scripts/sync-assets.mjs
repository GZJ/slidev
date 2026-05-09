import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const frontendRoot = path.resolve(scriptDir, "..");
const revealRoot = path.join(frontendRoot, "node_modules", "reveal.js");
const targetRoot = path.resolve(frontendRoot, "..", "src", "slidev", "assets", "reveal");

async function copyEntry(name) {
  await fs.cp(path.join(revealRoot, name), path.join(targetRoot, name), {
    recursive: true,
  });
}

async function main() {
  const packageJsonPath = path.join(revealRoot, "package.json");
  const packageJson = JSON.parse(await fs.readFile(packageJsonPath, "utf8"));

  await fs.rm(targetRoot, { recursive: true, force: true });
  await fs.mkdir(targetRoot, { recursive: true });

  for (const entry of ["dist", "LICENSE"]) {
    await copyEntry(entry);
  }

  const manifestPath = path.join(targetRoot, "manifest.json");
  const manifest = {
    package: packageJson.name,
    version: packageJson.version,
  };

  await fs.writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
  console.log(`Synced reveal.js ${packageJson.version} to ${targetRoot}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});