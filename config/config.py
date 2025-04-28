# config.py


# +++++++++++++ Variables +++++++++++++ #
LB_HOSTS            = ["10.250.239.251"]    # all machine hosts that the load-balancers could be found on
LB_PID_RANGE        = [0, 3]                # the range of PIDs that our single load-balancer can be instantiated with (V1: we'll have 1+ LBs) [start, end)
LB_BASE_PORT        = 6000                  # the base port for load-balancers (port = base_port + PID)
SERVER_HOSTS        = ["10.250.239.251"]    # all machine hosts that the servers could be found on
SERVER_PID_RANGE    = [0, 100]              # the range of PIDs that our servers can be instantiated with
SERVER_BASE_PORT    = 5000                  # the base port for servers (port = base_port + PID)
SERVER_REGIONS      = [0, 1, 2]             # the current geographic regions our app can serve, represented with number IDs
HEARTBEAT_TIMEOUT   = 4                     # number of seconds before we figure a server is down/dead
HEARTBEAT_INTERVAL  = 1                     # number of seconds in between servers send out a heartbeat
MAX_THREADS         = 25                    # each client requires 4 threads