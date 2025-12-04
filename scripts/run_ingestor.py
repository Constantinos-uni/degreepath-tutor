# Wrapper to run the ingestor module as a script from the project root
# Usage: python scripts\run_ingestor.py
import runpy

if __name__ == '__main__':
    # Run the package module as if using `python -m backend.ingestor`
    runpy.run_module('backend.ingestor', run_name='__main__')
