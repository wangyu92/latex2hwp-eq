## Summary

<!-- 1-3 lines on what changed and why. -->

## Coverage tier touched

- [ ] Tier 1 (frac, sqrt, sup/sub, sum/int/prod/lim, Greek, basic ops)
- [ ] Tier 2 (matrix/cases/decorators/text)
- [ ] Tier 3 (pile, color, font, displaystyle, 한글 변수)
- [ ] HWPX I/O (write/read paths, namespace, attributes)
- [ ] CLI / extraction / packaging
- [ ] Tests / CI only

## Manual visual check (한글 GUI)

CI can only verify XML structure and LaTeX↔EQS round-trips. Anything that
changes HWPX output or EQS emission must be opened in 한글 once:

- [ ] Generated `.hwpx` opens without errors.
- [ ] All equations render visually correct (no broken boxes, no error markers).
- [ ] Double-clicking each equation enters the equation editor with the EQS script.
- [ ] Copying an equation into another 한글 document works.
- [ ] N/A (CI/test/docs-only change)

한글 version + OS used: <!-- e.g. 한글 2024 / macOS 14 -->

## Ground-truth fixtures

- [ ] No new EQS patterns; existing fixtures still pass.
- [ ] Added new fixture(s) under `tests/fixtures/golden_hwpx/` and a regression test.
