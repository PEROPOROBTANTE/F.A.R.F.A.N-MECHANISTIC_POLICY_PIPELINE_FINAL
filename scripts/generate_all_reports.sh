#!/bin/bash
# Generate All Reports (MICRO, MESO, MACRO)
# Usage: bash scripts/generate_all_reports.sh --input INPUT_FILE --output-dir OUTPUT_DIR

set -euo pipefail

# Default values
INPUT_FILE=""
OUTPUT_DIR="data/reports"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --input)
      INPUT_FILE="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 --input INPUT_FILE --output-dir OUTPUT_DIR"
      exit 1
      ;;
  esac
done

# Validate input
if [ -z "$INPUT_FILE" ]; then
  echo "Error: --input is required"
  echo "Usage: $0 --input INPUT_FILE --output-dir OUTPUT_DIR"
  exit 1
fi

if [ ! -f "$INPUT_FILE" ]; then
  echo "Error: Input file not found: $INPUT_FILE"
  exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "======================================================================"
echo "Generating Multi-Level Reports"
echo "======================================================================"
echo "Input: $INPUT_FILE"
echo "Output Directory: $OUTPUT_DIR"
echo "======================================================================"
echo ""

# Function to generate report
generate_report() {
  local level=$1
  local output_file=$2
  local description=$3
  
  echo "[$level] Generating: $description"
  
  if python3 -m saaaaaa.core.report_generator \
    --input "$INPUT_FILE" \
    --output "$output_file" \
    --level "$level" 2>&1 | grep -v "^$"; then
    echo "[$level] ✓ Generated: $description"
    return 0
  else
    echo "[$level] ✗ Note: Report generator CLI may not be implemented yet"
    echo "[$level]    You can generate reports via the orchestrator or API"
    return 1
  fi
}

# Generate reports
echo "Generating MICRO report (300 question-level analyses)..."
generate_report "micro" "$OUTPUT_DIR/micro_report.json" "MICRO - Question-level explanations"
echo ""

echo "Generating MESO report (60 policy-dimension clusters)..."
generate_report "meso" "$OUTPUT_DIR/meso_report.json" "MESO - Cluster analyses"
echo ""

echo "Generating MACRO report (overall classification)..."
generate_report "macro" "$OUTPUT_DIR/macro_report.json" "MACRO - Overall classification"
echo ""

echo "======================================================================"
echo "Report Generation Complete"
echo "======================================================================"
echo ""

if ls "$OUTPUT_DIR"/*.json >/dev/null 2>&1; then
  echo "Reports saved to: $OUTPUT_DIR"
  echo ""
  echo "Generated files:"
  ls -lh "$OUTPUT_DIR"/*.json
else
  echo "Note: Report files not found. This may indicate:"
  echo "  1. Report generator CLI is not yet implemented"
  echo "  2. Use the main orchestrator for end-to-end analysis:"
  echo ""
  echo "     python3 -m saaaaaa.core.ORCHESTRATOR_MONILITH \\"
  echo "       --input your_plan.pdf \\"
  echo "       --output-dir data/results \\"
  echo "       --mode full"
fi

echo ""
