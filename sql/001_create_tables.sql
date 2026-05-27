-- Target: PostgreSQL 16, database biodata (see docker-compose.yml)
-- Maps to FIELDNAMES in data/make_synth_data.py
-- Do not run automatically; apply manually when ready.

CREATE TABLE IF NOT EXISTS qc_injection (
    assay_run_id          TEXT NOT NULL,
    run_date              DATE NOT NULL,
    analyte               TEXT NOT NULL,
    matrix                TEXT NOT NULL,
    instrument_id         TEXT NOT NULL,
    sample_type           TEXT NOT NULL,
    level                 TEXT NOT NULL,
    replicate             SMALLINT NOT NULL,
    nominal_conc_ng_ml    NUMERIC(12, 4),
    back_calc_conc_ng_ml  NUMERIC(12, 4),
    peak_area_ratio       NUMERIC(12, 4),
    dilution_factor       SMALLINT NOT NULL DEFAULT 1,
    bias_pct              NUMERIC(8, 2),
    within_acceptance     CHAR(1),
    PRIMARY KEY (assay_run_id, sample_type, level, replicate),
    CONSTRAINT qc_injection_sample_type_chk
        CHECK (sample_type IN ('CAL', 'QC', 'BLK', 'DBL')),
    CONSTRAINT qc_injection_within_acceptance_chk
        CHECK (within_acceptance IS NULL OR within_acceptance IN ('Y', 'N')),
    CONSTRAINT qc_injection_replicate_chk
        CHECK (replicate >= 1)
);

CREATE INDEX IF NOT EXISTS idx_qc_injection_run_date
    ON qc_injection (run_date);

CREATE INDEX IF NOT EXISTS idx_qc_injection_assay_run_id
    ON qc_injection (assay_run_id);
