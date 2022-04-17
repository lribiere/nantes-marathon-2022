
.PHONY: conda_env dependencies viz-signal compute-sqi viz-sqi viz-feasibility-checks viz-filtering tests

conda_env:
	@conda create -n nantes-marathon-2022 python=3.10 -y

dependencies:
	@pip install -r requirements.txt

viz:
	@echo 'Starting viz'
	@streamlit run main.py

