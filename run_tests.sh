#!/bin/bash
# Simple test runner script for Elfa Tools

set -e

echo "🧪 Running Elfa Tools Test Suite"
echo "=================================="
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing..."
    pip install pytest pytest-cov
fi

# Run tests with coverage
echo "Running tests with coverage..."
pytest --cov=. --cov-report=term-missing --cov-report=html -v

echo ""
echo "✅ Tests complete!"
echo "📊 Coverage report: htmlcov/index.html"
