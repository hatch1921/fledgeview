import globals from "globals";
import js from "@eslint/js";
export default [
  js.configs.recommended,
  { files: ["app.js"], languageOptions: { ecmaVersion: 2023, sourceType: "script", globals: { ...globals.browser, exifr: "readonly", JSZip: "readonly", UTIF: "readonly" } },
    rules: {
      "no-empty": ["warn", { allowEmptyCatch: true }],
      "no-unused-vars": ["warn", { args: "none", caughtErrors: "none" }],
      "no-shadow": "warn", "no-unused-expressions": ["warn", { allowShortCircuit: true, allowTernary: true }],
      "no-loop-func": "warn", "no-implicit-coercion": "off", "eqeqeq": ["warn", "smart"], "no-var": "warn", "prefer-const": "off",
      "no-unmodified-loop-condition": "warn", "no-constant-binary-expression": "warn", "no-self-compare": "warn", "no-template-curly-in-string": "warn", "array-callback-return": "warn",
      "no-useless-escape": "warn", "no-async-promise-executor": "warn", "require-atomic-updates": "off",
    } }];
