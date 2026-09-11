# TASK_INV_IMPL_E00_S04 — Local `verify_release` Command

## Status

`IMPLEMENTED_AWAITING_LOCAL_VERIFICATION`

External implementation: `ZXYHtech/inventory#3`, branch `impl/e00-release-safety`.

Static hardening reviewed through inventory head `61d486d9c1323d65694e7d7c0f6f3078eaf60045`.

## Authoritative entry point

```bash
python3 tools/verify_release.py
```

Optional stress checks:

```bash
python3 tools/verify_release.py --include-stress
```

## Required gate coverage

The command orchestrates:

- Python bytecode/syntax checks for required E00 and core source files;
- schema migration tests;
- DB integrity tests;
- backup/recovery tests;
- manifest/off-host-copy tests;
- independent backup-job test;
- authentication/security regression;
- core workflow regression;
- recognition regression;
- warehouse-efficiency regression;
- Bash syntax checks when Bash is available;
- JavaScript syntax plus `test_client_routing.js` when Node is available.

## Static review hardening added after initial implementation

A follow-up review found that the first version filtered required test paths by existence, so an incomplete checkout could silently run fewer checks. This was corrected in commit `b671f674aa69ac3adb55429fe54f456ab9ea137b`:

- required Python tests now fail closed if a file is missing;
- required Python source files are not silently omitted from `py_compile`;
- deployment shell syntax is checked via `bash -n` when Bash is present;
- existing client-routing regression is executed, not merely parsed, when Node is present;
- `--require-node` and `--require-bash` can turn optional tool availability into strict operator gates.

## Acceptance mapping

- one repository-local authoritative command: implemented;
- no GitHub Actions dependency: implemented;
- missing required checks fail closed: implemented;
- existing regression suites preserved: implemented.

## Remaining gate

This story is not complete until the command is actually executed from a real checkout and returns `RELEASE VERIFICATION: PASS`.
