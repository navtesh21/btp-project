"""
bgfusion
========
A clean-room implementation of the full three-stage pipeline from

    Li et al., "Noninvasive Blood Glucose Monitoring Using Spatiotemporal ECG and PPG
    Feature Fusion and Weight-Based Choquet Integral Multimodel Approach",
    IEEE TNNLS 35(10), 2024.

built on the PhysioCGM dataset, which carries ECG *and* PPG against a Dexcom CGM
reference and therefore supports every stage of the paper's design.

    stage1_data.py            Level 1  - load ECG + PPG, align clocks, filter, window
    stage2_temporal.py        Level 2a - db4 DWT temporal statistical features
    stage2_morphological.py   Level 2b - spatial morphological features
    stage2_fusion.py          Level 2c - feature fusion + selection
    stage3_fusion.py          Level 3  - 3 models -> Choquet integral -> BG output
    evaluate.py               leakage-controlled evaluation + clinical metrics

The modules `features_temporal`, `choquet`, `metrics`, `error_grid` and `base_models`
are the paper's mathematics and are dataset-independent; they were verified by hand
during the earlier D1NAMO study (see ../legacy_d1namo/) and are reused unchanged.
"""
