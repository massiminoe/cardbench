main:
	PYTHONPATH=. python src/main.py

run_tournament:
	PYTHONPATH=. python src/tournament.py

test:
	pytest tests/

demo_results:
	cd scripts && python3 analyze_tournament.py ../results/gin_rummy_v1