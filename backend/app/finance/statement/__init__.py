"""
Bank Statement Intelligence & Ingestion Package
Provides deterministic extraction, normalization, deduplication, and reconciliation
for CSV, XLSX, and PDF bank statements across Indian financial institutions.
"""

from app.finance.statement.normalizer import StatementNormalizer
from app.finance.statement.csv_parser import parse_csv_statement
from app.finance.statement.xlsx_parser import parse_xlsx_statement
from app.finance.statement.pdf_parser import parse_pdf_statement
from app.finance.statement.pipeline import StatementPipeline

__all__ = [
    "StatementNormalizer",
    "parse_csv_statement",
    "parse_xlsx_statement",
    "parse_pdf_statement",
    "StatementPipeline",
]
