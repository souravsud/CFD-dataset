#!/usr/bin/env python3
"""
Main entry point for CFD dataset generation pipeline.
This is a wrapper that delegates to the GenerateInputs module.
"""
import sys
import os

# Add GenerateInputs directory to path
generate_inputs_dir = os.path.join(os.path.dirname(__file__), 'GenerateInputs')
sys.path.insert(0, generate_inputs_dir)

from generateInputs import main

if __name__ == "__main__":
    main()