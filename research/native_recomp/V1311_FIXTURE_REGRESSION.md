# V1311: correct V1309 regression construction

V1309 CI correctly refused the synthetic fixture: 33 words rather than 32. The V1307 original construction had 32 (nine scalar stores, one stmw, 21 NOPs, one return); the previous manual count was wrong. Calculate padding from actual list length, and mutate the actual stmw at index nine. No private code or owner lane changed. Re-run source tests.
