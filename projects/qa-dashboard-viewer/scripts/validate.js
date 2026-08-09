const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const required = ["index.html", "styles.css", "app.js"];
const missing = required.filter((file) => !fs.existsSync(path.join(root, file)));

if (missing.length) {
  console.error(`Missing viewer file(s): ${missing.join(", ")}`);
  process.exit(1);
}

const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
for (const file of ["styles.css", "app.js"]) {
  if (!html.includes(file)) {
    console.error(`index.html does not reference ${file}`);
    process.exit(1);
  }
}

console.log("QA dashboard viewer static build validated.");
