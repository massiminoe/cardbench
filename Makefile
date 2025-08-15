main:
	PYTHONPATH=. python src/main.py

run_tournament:
	PYTHONPATH=. python src/tournament.py

test:
	pytest tests/