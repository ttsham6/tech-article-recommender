import { existsSync } from "fs";
import { basename, resolve } from "path";

const COMPONENTS_DIR = __dirname;
const INFRA_DIR = resolve(COMPONENTS_DIR, "..");
const REPO_ROOT = resolve(INFRA_DIR, "..");

export function resolveArtifactPath(path: string): string {
    const fileName = basename(path);
    const candidates = [
        resolve(process.cwd(), path),
        resolve(INFRA_DIR, path),
        resolve(REPO_ROOT, path),
        resolve(INFRA_DIR, "dist", fileName),
    ];

    for (const candidate of candidates) {
        if (existsSync(candidate)) {
            return candidate;
        }
    }

    throw new Error(`Artifact not found: ${path}`);
}
