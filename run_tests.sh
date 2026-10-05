#!/bin/bash
# 运行所有单元测试

echo "Running tests..."
pytest tests/ -v --tb=short --cov=. --cov-report=html --cov-report=term-missing

echo ""
echo "Test summary:"
echo "- Verbose output: -v"
echo "- Brief traceback: --tb=short"
echo "- Coverage report: HTML and terminal"
echo ""
echo "Coverage report available at: coverage_html/index.html"
echo "To run all tests and view coverage:"
echo "  pytest tests/ -v --cov=src --cov-report=html"
