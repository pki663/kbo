../python_venv/cwp/Scripts/Activate.ps1
python "manually.py"
python "cwp_simulator.py" -p 16 --game_path 'data/completed_games.pkl' --probability_path 'data/uniform_probability.pkl' --standing_path 'data/standing.pkl' --comingup_path 'data/comingup_games.pkl' --cli_path 'data/li.pkl' --probability_output 'data/uniform_probability.pkl' --standing_output 'data/standing.pkl' --cli_output 'data/li.pkl'
python "cwp_simulator.py" -p 16 --game_path 'data/completed_games.pkl' --probability_path 'data/log5_probability.pkl' --standing_path 'data/standing.pkl' --probability_output 'data/log5_probability.pkl' --standing_output 'data/standing.pkl' --winratio 'data/win_setting/2023_log5.pkl'
python "cwp_simulator.py" -p 16 --game_path 'data/completed_games.pkl' --probability_path 'data/pythagorean_probability.pkl' --standing_path 'data/standing.pkl' --probability_output 'data/pythagorean_probability.pkl' --standing_output 'data/standing.pkl' --winratio 'pythagorean'
python "preprocess_deploy.py"