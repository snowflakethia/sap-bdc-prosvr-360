import fs from "node:fs";
import crypto from "node:crypto";
import jwt from "jsonwebtoken";
import { isSpcs, resolveHome, SPCS_TOKEN_PATH } from "./snowflake.js";

let cachedPrivateKey: string | null = null;
function getPrivateKey(): string {
  if (!cachedPrivateKey) cachedPrivateKey = fs.readFileSync(resolveHome(process.env.SNOWFLAKE_PRIVATE_KEY_PATH ?? ""), "utf-8");
  return cachedPrivateKey;
}

/** Local-dev key-pair JWT for the Snowflake REST API (same key as the SQL session). */
function generateJwt(): string {
  const account = (process.env.SNOWFLAKE_ACCOUNT ?? "").toUpperCase().replace(/\..*$/, "");
  const user = (process.env.SNOWFLAKE_USER ?? "").toUpperCase();
  const pubDer = crypto.createPublicKey(getPrivateKey()).export({ type: "spki", format: "der" });
  const fingerprint = crypto.createHash("sha256").update(pubDer).digest("base64");
  const qualifiedUser = `${account}.${user}`;
  const now = Math.floor(Date.now() / 1000);
  return jwt.sign({ iss: `${qualifiedUser}.SHA256:${fingerprint}`, sub: qualifiedUser, iat: now, exp: now + 3540 },
    getPrivateKey(), { algorithm: "RS256" });
}

/** REST host: the SPCS-injected host, an explicit override, or <account>.snowflakecomputing.com. */
export function restHost(): string {
  if (process.env.SNOWFLAKE_REST_HOST) return process.env.SNOWFLAKE_REST_HOST;
  if (isSpcs() && process.env.SNOWFLAKE_HOST) return process.env.SNOWFLAKE_HOST;
  const account = (process.env.SNOWFLAKE_ACCOUNT ?? "").toLowerCase().replace(/_/g, "-");
  return `${account}.snowflakecomputing.com`;
}

/** Authorization headers for REST calls: SPCS OAuth token in the service, key-pair JWT locally. */
export function restAuthHeaders(): Record<string, string> {
  if (isSpcs()) {
    return {
      Authorization: `Bearer ${fs.readFileSync(SPCS_TOKEN_PATH, "ascii")}`,
      "X-Snowflake-Authorization-Token-Type": "OAUTH",
    };
  }
  return { Authorization: `Bearer ${generateJwt()}`, "X-Snowflake-Authorization-Token-Type": "KEYPAIR_JWT" };
}
