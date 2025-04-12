# config.py


# +++++++++++++ Variables +++++++++++++ #
LB_HOSTS            = ["127.0.0.1"]         # all machine hosts that the load-balancers could be found on
LB_PID_RANGE        = [0, 100]              # the range of PIDs that the load-balancers could be found on (for V0, we're only making ONE LB)
LB_BASE_PORT        = 6000                  # the base port for load-balancers (port = base_port + PID)
SERVER_BASE_PORT    = 5000                  # the base port for servers (port = base_port + PID)
SERVER_REGIONS      = [0, 1, 2]             # the current geographic regions our app can serve, represented with number IDs
