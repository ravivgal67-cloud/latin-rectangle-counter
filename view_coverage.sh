#!/bin/bash
# Script to run tests with coverage and open the HTML report

echo "Running tests with coverage..."
pytest

echo ""
echo "Opening coverage report..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open htmlcov/index.html
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open htmlcov/index.html
else
    echo "Coverage report generated at: htmlcov/index.html"
fi
