import https from "node:https";
import { Button } from "@mui/material";

export function insecureAgent(): https.Agent {
  return new https.Agent({ rejectUnauthorized: false });
}

export { Button };
