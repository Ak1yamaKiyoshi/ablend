source env/bin/activate
#export CC=gcc-15
#export CXX=g++-15
cd ./submodules/ardupilot/
python3 Tools/autotest/sim_vehicle.py --console -v ArduCopter --out=udp:127.0.0.1:14560 --out=udp:127.0.0.1:14561

