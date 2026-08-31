import https from "node:https";
import { Button } from "@barracuda-internal/bds-core";

export function secureAgent(): https.Agent {
  return new https.Agent({ rejectUnauthorized: true });
}

export { Button };
