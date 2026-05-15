# Coverage Baseline — Phase 2

Measured: 2026-05-16

| Metric | Value |
| --- | --- |
| Tool | `pytest-cov` |
| Target | `mcp/` package (all submodules) |
| Test set | `mcp/tests/` (271 tests, 0 failures) |
| Statement coverage | 86.10% (3634 statements, 505 missed) |
| Branch coverage | not measured (statement coverage only at this stage) |

## Adopted floor

The Phase-2 CI gate sets `[tool.coverage.report] fail_under` to
`max(85, baseline)` = `86%`. The floor is monotonic — Phase 3 and
later may raise it but never lower it.

## Known coverage gaps

| Module | Coverage | Notes |
| --- | --- | --- |
| `mcp/legal_texts/normalizer.py` | 0% | Untested helper; consider test-gap audit follow-up |
| `mcp/parser.py` | 61% | 86 missed statements; complex parser branches |
| `mcp/legal_texts/importer.py` | 65% | 29 missed statements |
| `mcp/legal_texts/runtime.py` | 79% | 15 missed statements |
| Other modules | 83–100% | Healthy |

## Raw output (tail)

```text
---------- coverage: platform darwin, python 3.12.3-final-0 ----------
Name                                     Stmts   Miss  Cover   Missing
----------------------------------------------------------------------
mcp/__init__.py                              0      0   100%
mcp/config.py                               13      0   100%
mcp/http_api.py                             46      0   100%
mcp/http_models.py                          56      0   100%
mcp/legal_texts/__init__.py                  0      0   100%
mcp/legal_texts/dataset.py                 143     17    88%   20, 26, 74, 82, 116, 128, 159-160, 162, 192-194, 196, 233-234, 241, 254
mcp/legal_texts/errors.py                   53      6    89%   47, 83, 85, 115-117
mcp/legal_texts/eu_neighbors.py            145     23    84%   22, 24, 27, 60, 64, 68, 71, 76, 78, 80, 82, 85, 88, 92, 102, 104, 131, 136, 219-222, 237
mcp/legal_texts/eurlex_xml.py               66      9    86%   32, 56, 90-92, 101, 114-116
mcp/legal_texts/gii_bulk.py                191      8    96%   116-117, 121, 230, 448, 450, 476, 500
mcp/legal_texts/gii_toc.py                 176     13    93%   75-81, 192, 210-216, 390, 406, 440
mcp/legal_texts/gii_xml.py                  75      2    97%   19, 99
mcp/legal_texts/importer.py                 83     29    65%   29, 33-38, 46-47, 67, 132-170
mcp/legal_texts/manifest.py                321     51    84%   81, 110, 112, 116, 124, 127, 133, 135, 141-142, 147, 149, 151, 166, 172-173, 178, 180, 182, 186, 249, 257, 259, 267, 269, 277, 305, 307, 316, 318, 324-325, 329, 338, 359, 361, 367-368, 372, 376, 391, 396-397, 408, 411, 455-457, 462-463, 471
mcp/legal_texts/models.py                  111     18    84%   15, 32, 46, 57, 77-86, 98, 108, 117, 136
mcp/legal_texts/normalizer.py               24     24     0%   1-42
mcp/legal_texts/registry.py                 65      7    89%   43, 50-51, 54, 86, 88, 90
mcp/legal_texts/relationships.py           269     42    84%   82, 87, 91, 95, 105, 110, 128, 180, 200, 202, 204, 206, 208, 210, 221-222, 227-228, 230, 233, 235, 239, 242, 255-256, 259, 263, 266, 268, 270, 274, 278, 294-295, 307, 312, 314, 328, 331, 335, 352, 365
mcp/legal_texts/resolver.py                116     19    84%   35-36, 44, 47-48, 50, 120, 123, 136-140, 150, 152, 154, 164, 166, 174
mcp/legal_texts/runtime.py                  71     15    79%   29, 31-38, 46, 48, 53, 55, 99, 101
mcp/legal_texts/search.py                   79      4    95%   44-45, 62, 117
mcp/legal_texts/sources.py                  24      1    96%   72
mcp/legal_texts/state_law.py               429     26    94%   161, 229, 233, 246, 335-340, 365-377, 379-389, 514, 518, 683, 686, 731, 746, 775, 779, 803, 811, 814, 829
mcp/legal_texts/state_law_coverage.py      152     16    89%   26, 74, 77, 93-94, 102-103, 105, 107, 122, 128, 136, 157-158, 240, 249
mcp/legal_texts/state_law_inventory.py     130     22    83%   57, 64, 71, 73, 76, 83, 85, 88, 98-99, 131, 134, 147, 159, 161, 163-165, 168, 172, 174, 178, 186
mcp/legal_texts/validation.py              522     67    87%   98, 107, 124, 126, 141, 157, 171-172, 180-181, 202, 205, 217, 241, 243, 259-260, 269-270, 292, 298, 302, 308, 317, 326, 329, 340-341, 353, 360, 364, 367, 369, 371, 374, 378, 381, 388, 407-408, 411-412, 428, 431-432, 440-441, 451, 455, 468, 505, 513, 535, 577-578, 610, 614, 617, 619, 621, 625, 657, 668, 670, 688, 720, 723
mcp/parser.py                              218     86    61%   10-31, 50, 102-103, 174-215, 241-246, 253, 256, 281-283, 295-298, 310-321, 347-369, 386-387, 418, 434, 444-447
mcp/server.py                               56      0   100%
----------------------------------------------------------------------
TOTAL                                     3634    505    86%

Required test coverage of 86.0% reached. Total coverage: 86.10%

============================= 271 passed in 12.50s =============================
```
