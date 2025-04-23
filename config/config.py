# config.py


# +++++++++++++ Variables +++++++++++++ #
LB_HOSTS            = ["127.0.0.1"]         # all machine hosts that the load-balancers could be found on
LB_PID_RANGE        = [0, 100]              # the range of PIDs that our single load-balancer can be insantiated with (V1: we'll have 1+ LBs)
LB_BASE_PORT        = 6000                  # the base port for load-balancers (port = base_port + PID)
SERVER_HOSTS        = ["127.0.0.1"]
SERVER_PID_RANGE    = [0, 100]
SERVER_BASE_PORT    = 5000                  # the base port for servers (port = base_port + PID)
SERVER_REGIONS      = [0, 1, 2]             # the current geographic regions our app can serve, represented with number IDs
HEARTBEAT_TIMEOUT   = 4                     # number of seconds before we figure a server is down/dead
HEARTBEAT_INTERVAL  = 1                     # number of seconds in between servers send out a heartbeat
MAX_THREADS         = 25