source ../enviroments/current.sh
cd ../submodules/ardupilot/
python3 Tools/autotest/sim_vehicle.py --console -v ArduCopter --out=udp:127.0.0.1:14560 --out=udp:127.0.0.1:14561 --out=udp:127.0.0.1:14562

