#!/bin/bash

SESSION="drone_sim"
tmux new-session -d -s $SESSION

tmux send-keys -t $SESSION 'source ../enviroments/current.sh' C-m
tmux send-keys -t $SESSION './launch_sitl.sh ' C-m

sleep 1

tmux split-window -v -t $SESSION
tmux send-keys -t $SESSION 'source ../enviroments/current.sh' C-m
tmux send-keys -t $SESSION 'python3 ../src/mavlink_scripts/mavlink_to_blender_bridge.py' C-m

sleep 1
tmux split-window -h -t $SESSION
tmux send-keys -t $SESSION 'source ../enviroments/current.sh' C-m
tmux send-keys -t $SESSION '../submodules/blender ../src/blender_scenes/scene-simple.blend --python ../src/blender_scripts/move_camera_position_from_socket.py -w -p 0 0 1280 720 2>&1 | tee .blender.log' C-m


sleep 5
tmux select-pane -t $SESSION:0.0
tmux split-window -v -t $SESSION
tmux send-keys -t $SESSION 'source ../enviroments/current.sh' C-m
tmux send-keys -t $SESSION 'python3 ../src/mavlink_scripts/pid_althold.py' C-m

tmux attach-session -t $SESSION
