"""Entry point for Streamlit Cloud — loads Overview page."""
import runpy
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
runpy.run_path("0_📊_Overview.py", run_name="__main__")
