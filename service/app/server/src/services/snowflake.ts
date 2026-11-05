import snowflake from "snowflake-sdk";
import fs from "node:fs";
import path from "node:path";

let connection: snowflake.Connection | null = null;
let connectPromise: Promise<snowflake.Connection> | null = null;

/** SPCS injects an OAuth session token at this path when running inside a service. */
export const SPCS_TOKEN_PATH = "/snowflake/session/token";

export function isSpcs(): boolean {
  return fs.existsSync(SPCS_TOKEN_PATH);
}

export function resolveHome(filePath: string): string {
  if (filePath.startsWith("~/")) {
    return path.join(process.env.HOME ?? "", filePath.slice(2));
  }
  return filePath;
}

function buildConnectionOptions(): snowflake.ConnectionOptions {
  const common = {
    clientSessionKeepAlive: true,
    account: process.env.SNOWFLAKE_ACCOUNT!,
    warehouse: process.env.SNOWFLAKE_WAREHOUSE ?? "WH_ACOCO_APP",
    application: "ACOCO_APP",
  };
  if (isSpcs()) {
    // Snowpark Container Services: the injected OAuth token runs as the service's owner role.
    const token = fs.readFileSync(SPCS_TOKEN_PATH, "ascii");
    return { ...common, host: process.env.SNOWFLAKE_HOST!, authenticator: "OAUTH", token } as snowflake.ConnectionOptions;
  }
  // Local development: key-pair (JWT) auth with the settings of connection <connection> (see .env.example).
  const privateKey = fs.readFileSync(resolveHome(process.env.SNOWFLAKE_PRIVATE_KEY_PATH ?? ""), "utf-8");
  return {
    ...common,
    username: process.env.SNOWFLAKE_USER!,
    privateKey,
    authenticator: "SNOWFLAKE_JWT",
    role: process.env.SNOWFLAKE_ROLE,
  };
}

function exec(conn: snowflake.Connection, sqlText: string, binds?: snowflake.Binds): Promise<Record<string, unknown>[]> {
  return new Promise((resolve, reject) => {
    conn.execute({
      sqlText,
      binds,
      complete(err, _stmt, rows) {
        if (err) reject(err);
        else resolve((rows ?? []) as Record<string, unknown>[]);
      },
    });
  });
}

function getConnection(): Promise<snowflake.Connection> {
  if (connectPromise) return connectPromise;
  connectPromise = new Promise((resolve, reject) => {
    const conn = snowflake.createConnection(buildConnectionOptions());
    conn.connect((err) => {
      if (err) {
        connectPromise = null;
        reject(err);
        return;
      }
      // Every app statement carries QUERY_TAG = 'ACOCO_APP' (fee-boundary evidence, PRD 8.2).
      exec(conn, "ALTER SESSION SET QUERY_TAG = 'ACOCO_APP'")
        .then(() => {
          connection = conn;
          resolve(conn);
        })
        .catch((sErr) => {
          connectPromise = null;
          reject(sErr);
        });
    });
  });
  return connectPromise;
}

/** Lowercase all column keys in a row object. */
function lowercaseKeys(row: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const key of Object.keys(row)) out[key.toLowerCase()] = row[key];
  return out;
}

/** Execute one statement with positional binds. Only the registry runner calls this. */
export async function runQuery(sql: string, binds?: snowflake.Binds): Promise<Record<string, unknown>[]> {
  try {
    return (await exec(await getConnection(), sql, binds)).map(lowercaseKeys);
  } catch (err) {
    if (!String(err).includes("terminated")) throw err;
    connection = null;
    connectPromise = null;
    return (await exec(await getConnection(), sql, binds)).map(lowercaseKeys);
  }
}

export async function destroy(): Promise<void> {
  if (!connection) return;
  return new Promise((resolve) => {
    connection!.destroy(() => {
      connection = null;
      connectPromise = null;
      resolve();
    });
  });
}
