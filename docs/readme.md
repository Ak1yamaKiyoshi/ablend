### setup 
Symlink your blender to submodules/ directory
- `ln -s /path/to/original_target /path/to/symlink_shortcut`
- `ln -s ~/bin/blender ./blender`

#### Create env
- `python3 -m venv env`
- `source env/bin/activate`

#### Clone Ardupilot to "submodules/"
- `cd submodules`
- `git clone https://github.com/ArduPilot/ardupilot.git`
- `git checkout Copter-4.6.3`
- `git submodule update --init --recursive`
- `pip install empy==3.3.4 future numpy pexpect pymavlink mavproxy`

##### if ubuntu:
`ardupilot/Tools/environment_install/install-prereqs-ubuntu.sh`

##### Install gcc15 if you have gcc16 only
For GCC 16 support check `https://github.com/ArduPilot/ardupilot/pull/32984`

```
sudo dnf install gcc15 gcc15-c++
```

```pip install -U pip packaging setuptools wheel
pip install -U future lxml pymavlink pyserial MAVProxy geocoder \
  empy==3.3.4 ptyprocess dronecan flake8 junitparser \
  numpy pyparsing psutil intelhex
```

##### if python 3.14.3 (pkg_resources deprecated, dronecan errors)
`pip install "setuptools<81"`

#### build waf 
if gcc16/15 installed, and 16 is not yet supported:
```
export CC=gcc-15
export CXX=g++-15
```

Then: 
- `./waf configure --board sitl`
- `./waf copter`

add symlink 
- `ln -s Tools/autotest/sim_vehicle.py`

### run 
Launch blender (which already has socket open) with:
- `python3 launch_blender.py`

Launch ardupilot sitl 
- `cd ./submodules/ardupilot/`
- `python3 Tools/autotest/sim_vehicle.py --console -v ArduCopter --out=udp:127.0.0.1:14560 --out=udp:127.0.0.1:14561`
