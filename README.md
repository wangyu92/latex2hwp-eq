# hwpx-eq

LaTeX ↔ HWPX 양방향 수식 변환기. 파일 in / 파일 out, 한글 앱 자동화 의존 없음.

## 기능

- **`tex2hwpx`**: LaTeX(.tex/.md) 파일에서 수식을 추출해 한글 HWPX 파일로 출력.
  사용자가 한글에서 그 파일을 열어 본문에 복사해 쓴다.
- **`hwpx2tex`**: 한글에서 작성한 .hwpx 파일에서 모든 수식을 추출해 LaTeX으로
  출력 (md/tex/plain 포맷).

지원 수식 (Tier 1 + Tier 2):

| 카테고리 | 예시 |
|---|---|
| 분수·근호 | `\frac{a}{b}`, `\sqrt{x}`, `\sqrt[n]{x}` |
| 첨자 | `a_i^n`, `a_{i+1}^{2n}` |
| 큰 연산자 | `\sum_{i=1}^n`, `\int_a^b`, `\prod`, `\lim`, `\oint`, `\iint` |
| 그리스 | `\alpha`…`\omega`, `\Gamma`…`\Omega` (소·대문자 풀세트) |
| 함수 | `\sin`, `\cos`, `\tan`, `\log`, `\ln`, `\exp`, `\arcsin`, `\sinh`, `\det`, `\max` 등 |
| 연산자·관계 | `\le \ge \ne \pm \mp \times \div \cdot \approx \equiv \in \subset` 등 |
| 괄호 | `\left( ... \right)` 5쌍 (`( ) [ ] \{ \} | \|`) |
| 행렬 | `matrix/pmatrix/bmatrix/vmatrix/Vmatrix` ↔ `\begin{matrix}…\end{matrix}` |
| cases | EQS `cases{값 & 조건 # 값 & 조건}` ↔ LaTeX `\begin{cases}` |
| 장식자 | `\hat \widehat \bar \overline \vec \dot \ddot \tilde` |
| 텍스트 | `\text{...}` ↔ EQS `rm "..."` |
| 한글 변수 | `{가}+{나}=다` 그대로 보존 |

## 설치

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
hwpx-eq --help
```

요구: Python ≥ 3.10.

## 사용

```bash
# LaTeX → HWPX
hwpx-eq tex2hwpx in.tex                  # → in.hwpx
hwpx-eq tex2hwpx in.tex -o out.hwpx
hwpx-eq tex2hwpx in.tex --mode all       # 파일 전체를 수식 1개로

# HWPX → LaTeX
hwpx-eq hwpx2tex doc.hwpx                # stdout, $$...$$ 형식
hwpx-eq hwpx2tex doc.hwpx -o out.md --format md
hwpx-eq hwpx2tex doc.hwpx --format plain # 한 줄에 한 수식
```

## 시나리오

**LaTeX → 한글:**
1. LaTeX이 든 `.tex` 또는 `.md` 파일 준비
2. `hwpx-eq tex2hwpx in.tex -o out.hwpx`
3. 한글에서 `out.hwpx` 열기 → 수식 객체로 변환되어 있음
4. 원하는 수식을 본문 문서에 복사·붙여넣기

**한글 → LaTeX:**
1. 한글 문서를 `.hwpx`로 저장
2. `hwpx-eq hwpx2tex doc.hwpx --format md`
3. 모든 수식이 `$$...$$` 블록으로 출력됨

## 한계

- HWP 바이너리(`.hwp`)는 미지원. 한글에서 "다른 이름으로 저장 → HWPX(*.hwpx)" 필요.
- 수식 위치/크기는 휴리스틱으로 산정 — 한글이 파일을 열 때 자동 재계산함.
- Tier 3 (pile/lpile/cpile 정렬, 색상, 폰트, displaystyle 메타) 미지원.
- 미지원 LaTeX 매크로는 EQS의 `rm "..."` 텍스트로 escape됨 (경고 로그).

## 개발

```bash
pytest                    # 147개 테스트
ruff check .              # 린트
ruff check . --fix        # 자동 수정
```

테스트 구조:
- `tests/test_eqs.py`, `tests/test_latex.py` — 단위 + 라운드트립
- `tests/test_hwpx_write.py`, `tests/test_hwpx_read.py` — HWPX I/O
- `tests/test_golden_hwpx.py` — 한글이 직접 만든 ground-truth 11개 회귀
- `tests/fixtures/golden_hwpx/` — 사용자가 한글에서 작성한 .hwpx 샘플
- `tests/fixtures/tier1_samples/` — 우리가 생성한 .hwpx 샘플 (시각 검증용)

새 수식 토큰을 추가할 땐 `src/hwpx_eq/mappings.py`의 단일 테이블만 수정하면
양방향이 동기화된다.

## 아키텍처

```
LaTeX ─pylatexenc─▶ IR (AST) ─emit─▶ EQS ─lxml inject─▶ .hwpx
.hwpx ─lxml XPath─▶ EQS ─hand-rolled parser─▶ IR ─emit─▶ LaTeX
```

자체 IR (AST)을 두 변환의 공통 표현으로 사용. MathML 경유 없음 — EQS의 한컴
특이 메타(`pile/cases`, `font="HYhwpEQ"`, `baseLine`/`baseUnit`)와 1:1 매핑이
어렵고 라운드트립 손실이 큼.

플랜 파일: `~/.claude/plans/latex-functional-fiddle.md`.
