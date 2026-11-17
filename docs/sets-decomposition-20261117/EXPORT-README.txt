Export of sets A and B for an independent recomputation (addendum 6130d44, item h; written by tools/sets_decompose.py
of 2d10dae from the checked archives of the runs). Files: export-A.npz, export-B.npz (numpy .npz, compressed).

Times: t = 0 (the run's input.sa) and t = 1.0, 1.1, ..., 4.0 Gyr: 32 snapshots (t = 0 plus the 31 of the request).
Particles: every test particle present at that time (not only S_BB).

Per particle and time (one row each; float32 unless noted):
  t       time in Gyr
  idx     particle index, int32, constant over time: test particle "tpNNNNN" of the run has idx NNNNN (0..63999)
  a       semi-major axis (au)
  e       eccentricity
  inc     inclination (deg)
  Omega   longitude of the ascending node (deg)
  omega   argument of pericentre (deg); varpi = (Omega + omega) mod 360
Per time (arrays snap_*, one value per snapshot, in the order of snap_t):
  snap_t                          time in Gyr
  snap_p9_a, snap_p9_e, snap_p9_inc, snap_p9_Omega, snap_p9_varpi   Planet Nine, same convention as the particles
  snap_jup_a, snap_jup_e          Jupiter (barycentric, mu = G * total mass of the massive bodies)
  snap_plane_inc, snap_plane_node Jupiter's orbital plane (its pole) relative to the run's frame, ecliptic J2000 (deg)

Convention (exactly as tools/prod_eval.py = prod-eval-v1 forms the elements for M1-M5, function frame_elements):
  barycentric osculating elements (centre and mu: the barycentre and the total mass of the massive bodies);
  angles in the frame of Jupiter's orbital plane at that snapshot (x to its ascending node on the ecliptic, z to
  its pole), with "dog-leg" longitudes: Omega and varpi are shifted by the node N of Jupiter's plane, so they count
  from the equinox along the ecliptic to N, then along Jupiter's plane;
  dvarpi = (varpi - snap_p9_varpi) mod 360 gives the dvarpi of prod_eval.py; q = a (1 - e).
  e, Omega and omega are derived from the values prod_eval.py forms (q, dOmega, dvarpi and Planet Nine's elements),
  not converted again from the states. float32 rounding: about 1e-5 deg in the angles.
S_BB as in the criteria: 150 < a < 1000 au, q > 42 au. The evaluation window is 1-4 Gyr; t = 0 is extra.
