# Status 2026-10-21: an open deviation in the validation

This note is a new file and changes none of the documents it refers to.

**Open, not explained:** R(Δϖ) of the distant test particles (a > 230 au,
q > 42 au) is lower with p9gpu than with MERCURIUS:

- 200-Myr comparison (`docs/validation-smooth-200myr.md`): at 200 Myr 0.545
  (p9gpu) against 0.608 (MERCURIUS), beyond 2 bootstrap standard errors.
- Ensemble (`docs/validation-ensemble-200myr.md`): at 200 Myr all four p9gpu
  runs (0.545, 0.575, 0.574, 0.581) below both MERCURIUS runs (0.608, 0.610);
  from about 135 Myr on all four below both at every time. The ensemble did
  not pass; by its criteria the difference counts as systematic.
- Up to about 130 Myr the two agree within the run-to-run scatter. R(ΔΩ),
  survivors, distributions and paired losses agree throughout.

Consequences: the validation of the smooth transition is not accepted; no
production run has been started; p9gpu is not changed until the cause is
known (decision of the project lead).

The cause is being searched (setup of both programs, IAS15 as a reference,
secular frequencies of the planets and the literature, precession rates of
the distant particles); its results go into new files. A first finding, not
yet a cause: the giant planets' secular frequencies of the MERCURIUS runs
(dt 0.5 yr) differ from IAS15 by 3e-5 to 3e-4 (phase drifts of 57 to 215
degrees in 200 Myr), those of p9gpu v5 (planets with 8 inner steps) by about
5e-6.
