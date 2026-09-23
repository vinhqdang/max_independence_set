# Editor's independent ground truth

Computed directly from `results/cor_main60.csv`, not from the manuscript.

## Wilcoxon: raw sizes (what the paper does) vs relative gap (what the paper says it does)

| baseline | p, raw sizes | Holm adj | p, relative gap | Holm adj |
|---|---|---|---|---|
| online_mis | 0.00001 | 0.0001 sig | 0.00001 | 0.0001 sig |
| lineartime | 0.00003 | 0.0002 sig | 0.00002 | 0.0001 sig |
| nearlinear | 0.00014 | 0.0005 sig | 0.00005 | 0.0002 sig |
| numvc | 0.00079 | 0.0024 sig | 0.15493 | 0.3099 **NS** |
| fastvc | 0.02998 | 0.0600 **NS** | 0.44062 | 0.4406 **NS** |
| redumis | 0.19506 | 0.1951 **NS** | 0.12682 | 0.3805 **NS** |

Paper claims significance over **five of six**. Raw sizes uncorrected: five. Raw sizes with Holm over the six comparisons: **four** (FastVC falls to p=0.060). On a scale-free relative gap: **three** (FastVC and NuMVC both non-significant).
