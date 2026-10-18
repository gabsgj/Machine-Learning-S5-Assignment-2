@echo off
cd /d "%~dp0"
py -3 capability_embedding.py --experiments --vectors --compose
