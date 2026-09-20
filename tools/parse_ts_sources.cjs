
const fs = require('fs');
const ts = require('typescript');
const targets = JSON.parse(process.argv[2]);
let failed = false;
for (const [file, kind] of targets) {
  let source = fs.readFileSync(file, 'utf8');
  if (kind === 'vue') {
    const match = source.match(/<script setup lang="ts">([\s\S]*?)<\/script>/);
    if (!match) {
      console.error(`FAIL ${file}: missing script setup`);
      failed = true;
      continue;
    }
    source = match[1];
  }
  const sf = ts.createSourceFile(file, source, ts.ScriptTarget.ES2020, true, ts.ScriptKind.TS);
  const errors = sf.parseDiagnostics ?? [];
  if (errors.length) {
    failed = true;
    for (const d of errors) {
      console.error(`FAIL ${file}: ${ts.flattenDiagnosticMessageText(d.messageText, '\n')}`);
    }
  } else {
    console.log(`PASS TS parse ${file}`);
  }
}
process.exit(failed ? 1 : 0);
