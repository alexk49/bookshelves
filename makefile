.PHONY: run clean
test:
	# run all tests in test folder
	.venv/bin/python3 -m unittest discover -v
setup:
	# setup script to run
	# make setup
	pip install -r requirements.txt
clean:
	# clean pycache
	# make clean
	rm -rf __pycache__
	rm -rf .venv
dist: .venv/bin/activate
	# convert to .exe for distribution
	pyinstaller --onefile real-code.py
.venv/bin/activate: requirements.txt
	# build venv
	# update venv if requirements is changed
	python3 -m venv .venv
	./.venv/bin/pip install -r requirements.txt
