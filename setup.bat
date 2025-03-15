@echo off
echo Setting up virtual environment...
python -m venv .venv

echo Activating virtual environment
call .venv\Scripts\activate

echo Installing dependencies
pip install -r requirements.txt

echo Setup complete. you only have to run this setup once, Just run main.py subsequently. 
echo Running main.py...
python main.py

echo Done
pause