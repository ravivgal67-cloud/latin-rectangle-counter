#!/bin/bash
# Quick coverage summary without running full test suite

if [ ! -f ".coverage" ]; then
    echo "No coverage data found. Run 'pytest' first."
    exit 1
fi

echo "=== Code Coverage Summary ==="
echo ""
coverage report --skip-covered --sort=cover
echo ""
echo "For detailed HTML report, run: ./view_coverage.sh"
