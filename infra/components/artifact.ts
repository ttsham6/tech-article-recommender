import { createHash } from "crypto";
import { readFileSync } from "fs";
import { basename } from "path";

export function getArtifactHash(path: string): string {
    return createHash("sha256").update(readFileSync(path)).digest("hex").slice(0, 16);
}

export function getVersionedArtifactKey(path: string): string {
    const hash = getArtifactHash(path);
    const fileName = basename(path);
    return `${hash}-${fileName}`;
}
