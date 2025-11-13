#!/bin/bash
# Run All Producer Modules in Parallel
# Usage: bash scripts/run_all_producers.sh --input INPUT_FILE --output-dir OUTPUT_DIR

set -euo pipefail

# Default values
INPUT_FILE=""
OUTPUT_DIR="data/producers"
PARALLEL=true

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
    --sequential)
      PARALLEL=false
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 --input INPUT_FILE --output-dir OUTPUT_DIR [--sequential]"
      exit 1
      ;;
  esac
done

# Validate input
if [ -z "$INPUT_FILE" ]; then
  echo "Error: --input is required"
  echo "Usage: $0 --input INPUT_FILE --output-dir OUTPUT_DIR [--sequential]"
  exit 1
fi

if [ ! -f "$INPUT_FILE" ]; then
  echo "Error: Input file not found: $INPUT_FILE"
  exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "======================================================================"
echo "Running All Producer Modules"
echo "======================================================================"
echo "Input: $INPUT_FILE"
echo "Output Directory: $OUTPUT_DIR"
echo "Mode: $([ "$PARALLEL" = true ] && echo "Parallel" || echo "Sequential")"
echo "======================================================================"
echo ""

# Function to run a producer
run_producer() {
  local producer_num=$1
  local module=$2
  local output_file=$3
  local description=$4
  
  echo "[$producer_num] Starting: $description"
  
  if python3 -m "$module" \
    --input "$INPUT_FILE" \
    --output "$output_file" 2>&1 | grep -v "^$"; then
    echo "[$producer_num] ✓ Completed: $description"
    return 0
  else
    echo "[$producer_num] ✗ Failed: $description (module may not support CLI)"
    return 1
  fi
}

# Producer configurations
declare -a PRODUCERS=(
  "1|saaaaaa.analysis.financiero_viabilidad_tablas|producer_1_financial.json|Financial Viability & Causal DAG"
  "2|saaaaaa.analysis.Analyzer_one|producer_2_semantic.json|Semantic Cube & Value Chain"
  "3|saaaaaa.analysis.contradiction_deteccion|producer_3_contradictions.json|Contradictions & Coherence"
  "4|saaaaaa.processing.embedding_policy|producer_4_embedding.json|Semantic Search & Bayesian"
  "5|saaaaaa.analysis.teoria_cambio|producer_5_toc.json|DAG Validation & Monte Carlo"
  "6|saaaaaa.analysis.dereck_beach|producer_6_beach.json|Beach Tests & Mechanisms"
  "7|saaaaaa.processing.policy_processor|producer_7_patterns.json|Pattern Matching & Evidence"
)

# Run producers
if [ "$PARALLEL" = true ]; then
  echo "Launching all producers in parallel..."
  echo ""
  
  # Launch all producers in background
  for config in "${PRODUCERS[@]}"; do
    IFS='|' read -r num module output desc <<< "$config"
    (run_producer "$num" "$module" "$OUTPUT_DIR/$output" "$desc") &
  done
  
  # Wait for all to complete
  wait
  
else
  echo "Running producers sequentially..."
  echo ""
  
  for config in "${PRODUCERS[@]}"; do
    IFS='|' read -r num module output desc <<< "$config"
    run_producer "$num" "$module" "$OUTPUT_DIR/$output" "$desc"
    echo ""
  done
fi

echo ""
echo "======================================================================"
echo "Producer Execution Complete"
echo "======================================================================"
echo "Results saved to: $OUTPUT_DIR"
echo ""
echo "Files created:"
ls -lh "$OUTPUT_DIR"/*.json 2>/dev/null || echo "  (Note: Some producers may not have CLI support yet)"
echo ""
