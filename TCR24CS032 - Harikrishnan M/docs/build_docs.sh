#!/bin/bash
set -e

echo "Building Formal Design Specification..."
pdflatex -interaction=nonstopmode formal_design.tex

echo "Building Technical Report (Deliverable 4)..."
pdflatex -interaction=nonstopmode technical_report.tex

echo "Documentation built successfully."