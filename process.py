import pandas as pd
import psycopg2

# -------------------------------------------------------
# STEP 1 — Read the CSV file
# -------------------------------------------------------
# pd.read_csv() opens a CSV file and loads it into a
# "DataFrame" — think of a DataFrame as an in-memory table,
# like a spreadsheet tab held in Python's memory.
#
# Replace "synthetic_data.csv" with whatever your CSV file
# is actually named. It must be in the same folder as this
# script, or you must give the full path.
# -------------------------------------------------------

csv_df = pd.read_csv("data/synth/qc_runs_a.csv")

print("CSV loaded. Rows:", len(csv_df))
print(csv_df.head())   # shows the first 5 rows so you can confirm it loaded


# -------------------------------------------------------
# STEP 2 — Connect to Postgres and pull the reference table
# -------------------------------------------------------
# psycopg2.connect() opens a connection to your local
# Postgres database running in Docker.
#
# host="localhost"   — your own machine
# port=5432          — the standard Postgres door number
# dbname             — the name of the database you created
# user / password    — whatever you set when you loaded data
#
# Change these values to match what YOU used when you set
# up Postgres in the last step.
# -------------------------------------------------------

conn = psycopg2.connect(
    host="localhost",
    port=5433,  # Docker maps 5433→5432 (5432 is used by another Postgres on this machine)
    dbname="biodata",       # <-- change this to your database name
    user="appuser",     # <-- change this to your username
    password="localpass"  # <-- change this to your password
)

# pd.read_sql() runs a SQL query and loads the result
# into another DataFrame.
# "SELECT * FROM reference_table" means:
#   SELECT = give me data
#   *      = all columns
#   FROM reference_table = from this table
# Change "reference_table" to whatever your table is called.

ref_df = pd.read_sql("SELECT * FROM qc_injection", conn)

conn.close()  # always close the connection when you are done with it

print("Reference table loaded. Rows:", len(ref_df))
print(ref_df.head())


# -------------------------------------------------------
# STEP 3 — Merge the two tables together
# -------------------------------------------------------
# pd.merge() joins two DataFrames on a shared column —
# exactly like a VLOOKUP or SQL JOIN.
#
# left=csv_df        — the first table (your CSV data)
# right=ref_df       — the second table (your Postgres data)
# on="sample_id"     — the column name that exists in BOTH
#                      tables and links them together.
#                      Change "sample_id" to whatever your
#                      shared column is actually called.
# how="left"         — keep all rows from the CSV even if
#                      there is no match in the reference table
# -------------------------------------------------------

merged_df = pd.merge(
    left=csv_df,
    right=ref_df,
    on="assay_run_id",   # <-- change this to your shared column name
    how="left"
)

print("Merged. Rows:", len(merged_df))


# -------------------------------------------------------
# STEP 4 — Sort the merged table
# -------------------------------------------------------
# sort_values() reorders the rows.
# by="sample_id"     — sort by this column.
#                      Change to whichever column makes
#                      sense for your data.
# ascending=True     — A to Z, smallest to largest.
#                      Set to False to reverse.
# -------------------------------------------------------

sorted_df = merged_df.sort_values(by="assay_run_id", ascending=True)


# -------------------------------------------------------
# STEP 5 — Write out to Excel
# -------------------------------------------------------
# to_excel() saves the DataFrame as an .xlsx file.
# "output_report.xlsx" is the name of the file it creates.
# index=False means: do NOT add a row-number column on the
# left side (that column would just be 0, 1, 2... and you
# don't need it in the report).
# -------------------------------------------------------

sorted_df.to_excel("output_report.xlsx", index=False)

print("Done. File saved as output_report.xlsx")