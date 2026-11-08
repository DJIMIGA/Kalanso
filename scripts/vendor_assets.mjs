// Copie les scripts tiers depuis node_modules vers static/vendor/, pour qu'ils soient servis par
// l'application et jamais par un CDN. Lancer avec `npm run vendor` (inclus dans `npm run build`).
import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const target = join(root, "static", "vendor");
mkdirSync(target, { recursive: true });

const files = [
  { pkg: "htmx.org", source: "dist/htmx.min.js", name: "htmx.min.js" },
  { pkg: "alpinejs", source: "dist/cdn.min.js", name: "alpine.min.js" },
];

const versions = {};
for (const file of files) {
  const pkgDir = join(root, "node_modules", file.pkg);
  copyFileSync(join(pkgDir, file.source), join(target, file.name));
  versions[file.name] = JSON.parse(readFileSync(join(pkgDir, "package.json"), "utf8")).version;
}
writeFileSync(join(target, "VERSIONS.json"), JSON.stringify(versions, null, 2) + "\n");
console.log("Scripts copiés dans static/vendor/ :", versions);
