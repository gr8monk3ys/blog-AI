frontend:
	cd frontend &&
	streamlit run Home.py

backend:
	python3 -m venv env &&
	source env/bin/activate &&
	pip3 install --upgrade pip
	pip3 install -r requirements.txt
	