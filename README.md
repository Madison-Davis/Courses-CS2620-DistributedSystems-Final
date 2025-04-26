# CS 2620 Final Project

-------------------------------------------
## Motivation
Animal shelters are often imbalanced, where some shelters are overflowing their capacity and others are sparsely populated.  This not only includes donatable items, but occupants as well.  There currently does not exist any centralized application for animal shelters to communicate efficiently with each other across geographical regions.  As to date, most shelters communicate via text or email to one another and in relatively disconnected ways.  Therefore, we wanted to develop a distributed application that allows animal shelters in the same area to efficiently navigate capacity balancing.


-------------------------------------------
## Objective
This site builds application for animal shelters to request to send dogs between each other. When registering as a new account on the application, the animal shelter will denote which region they belong to (East = 0, Midwest = 1, West = 2).  Shelters can then communicate with other shelters in the same region and request to send a certain number of dogs to other shelters if they are reaching or surpassing their capacity.  Then, the recipient shelter will approve or deny the request, depending on their current capacity.  The complexity of this project comes from multiple leader servers managing each geographical instance of this “game,” and when servers fail, a load balancer must decide which alternative leader they must send all the clients of that particular region to.



-------------------------------------------
## Setup

Clone the repository.
Generate Python gRPC files: Navigate to the root project directory and run `py -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/app.proto`

Set configuration information in `config.py`:
- Hosts: base and range
- Ports: base and range
- Regions: possible integers
- Heartbeat: timeout and interval
- Threads: higher max can support more clients

Run load balancer:
`py -m load_balancer.load_balancer --host=HOST --pid=PID`
- HOST: valid host, e.g. 127.0.0.1
- PID: integer at least 0

Run server:
`py -m server.server_app --host=HOST --region=REGION`
- HOST: valid host, e.g. 127.0.0.1
- REGION: integer in {0, 1, 2}

Run client GUI:
`py -m client.gui`

Run unit tests:
`py -m unittest tests.tests`


-------------------------------------------
## Code Structure

```
├── client
│   ├── client_app.py           → AppClient class, functions to request/receive from server
│   ├── gui.py                  → creates GUI for client
├── proto
│   ├── app.proto               → defines gRPC services and messages for requests/responses
│   ├── app_pb2.py              → generated code from compiler: for all .proto service/rpc defs
│   ├── app_pb2_grpc.py         → generated code from compiler: for all .proto message defs
├── config
│   ├── config.py               → defines HOST/PORT and other parameters
├── server
│   ├── server_app.py           → AppService class, functions to use SQL and return results
│   ├── server_security.py      → for password hashing
├── load_balancer
│   ├── load_balancer.py        → functions for the load balancer
├── databases
│   ├── lb_pid.py               → database for each load balancer of pid (#)
│   ├── server_pid_reg.py       → database for each server of pid (#) and region (#)
├── tests
│   ├── unit_tests.py           → unit tests
│   ├── integration_tests.py    → integration tests
└── README.md
```


-------------------------------------------
## Assumptions
1. For testing purposes, we have 3 servers and will not be making new ones.  
2. For servers, we start with one server per region, which is the leader.  For just proof of concept, we will not have ‘replicas’ of servers.  Rather, each server of a region it is not currently serving serves as that region’s backup.
3. For clients, their shelter capacity is hidden for data privacy reasons.  Moreover, shelters can not change their region (they are physical locations and often will not change locations across the country).  
4. For broadcasts, they are all or nothing (as in if a shelter requests 3 dogs, a recipient shelter must accept all 3 dogs, not just 1 or 2).  Broadcasts are just sent out to the shelter’s designated region.
5. For load balancers, the 'number of clients' variable it keeps for each region is the number of active clients.





-------------------------------------------
## GUI Design

<img width="600" alt="Screenshot 2025-04-24 at 10 13 34 AM" src="https://github.com/user-attachments/assets/f83ad1ce-147e-4b0a-949f-dd7591fcbb68" />

Picture here is our login frame GUI design.  It has a dropdown of choosing to log in as a new user or a returning.  If new, the client inputs a username, password, and a region (East = 0, Midwest = 1, West = 2).  If the username exists, an error pops up informing them that the username already exists.  If returning, the client only puts in their username and password.  

<img width="600" alt="Screenshot 2025-04-24 at 10 13 46 AM" src="https://github.com/user-attachments/assets/c995c42f-30f1-4515-940e-06fadcbce732" />


Picture here as an image is our main frame GUI design.  It provides a space on the left for shelter information and statistics, such as total capacity and dog count.  For dog count, it is automatically updated during an accepted broadcast, and can also be manually updated if the shelter individually receives more dogs.  The middle space shows a map of shelters.  It is dynamic in the sense that a dot shows up in a part of the map based on the inputted region (3 regions total, as seen from the 3 figures in the map).  The right side shows a place to ask for a broadcast, a table of all your previous broadcasts and their status (pending/approved/denied), and broadcasts you received from other shelters in your region (whereupon you can accept or deny it).  If you accept or deny, for a short time it says ‘pending’.  This is for the case where two shelters simultaneously respond to the broadcast; the client will determine which was earlier and go with that response, whereupon the accept/reject button will be greyed out on all other shelters’ received broadcasts, indicating that this request has been served.





-------------------------------------------
## Protocol Design

We utilized gRPC to design how messages were to be sent to/from the client/server.  We encourage you to look into the `app.proto` file for the complete list of all of our services and messages.  We will highlight the main ones here.



-------------------------------------------
## Database Design

Format: [COLUMN]: [TYPE]

Each server maintains a database with the following tables:

Accounts Table
1. uuid: integer primary key autoincrement
2. username: text
3. region: integer in {0, 1, 2}
4. dogs: integer
5. capacity: integer                    // arbitrarily initialized to 30
6. pwd_hash: text
   
Broadcasts Table
1. broadcast_id: integer
2. recipient_id: integer
3. sender_username: text
4. sender_id: integer
5. amount_requested: integer
6. status: integer in {0, 1, 2, 3}      // 0: denied, 1: pending, 2: deleted, 3: approved

Registry Table
1. pid: integer primary key
2. timestamp: real
3. address: text

Each load balancer maintains a database with the following tables:

Regions Table:
1. region_id: integer primary key
2. server_pid: integer foreign key

Servers Table:
1. pid: integer primary key
2. address: text
3. load: integer
4. status: bool

Registry Table
1. pid: integer primary key
2. timestamp: real
3. address: text

-------------------------------------------
## Data Transfer Design
We have three main data transfers:
1. Initialization: the initialization stage requires the use of a config file.  The config file has the list of all IP addresses that both LBs and servers can be found on, a base port (integer) for the LBs (6000) and servers (5000), and a range of PIDs that both LBs and servers could have.  The full address of these machines is therefore notated as IP address : port, where the port is the base port plus the machine’s PID.  The LB starts up without any prerequisites.  When the server starts up, it will use the config file to iteratively ping all possible LBs, starting from the lowest-PID LB, until it hears back from a LB.  The LB will hear the new server, place it in its registry of servers, then ping all other servers to update their database registry of servers.  When one of these existing servers updates, if any, it will tell the LB all of its data.  The LB will then return the data as a response to the new server.  This new server will therefore be caught up.  The LB will also return a new PID for the server based on the LB’s database of registered and active servers; PIDs start at 0 and increment when adding more servers to the existing pile of servers.  When a client starts up, it will also ping over all possible LBs.  When it finds one that is alive, it will request “I am in region x, what server should I contact?”.  The LB will look in its regions database, determine which server should be serving that region, and return the data to the client, whereupon the client is all set up to start communicating.
2. Data Replication: when a server for a specific region updates its tables from some operation (for example, new client, deleted client, new broadcast), it must propagate the changes to the other servers’ databases.  In its Replicate function, it will format data so that it mimics the update that it itself had to do, and it will send out this request to all other servers.  The servers will conduct that change in their database and return a success message upon successfully conducting the same operation in their database.
3. Server Failure: if a server dies (CTRL+C in terminal), the other servers will detect this because their heartbeat messages will not be returned.  After a specified threshold of time (config file), the servers will contact the LB telling it that a specific server died.  The LB will do the following: it will delete that server from its database, then re-assign its clients to the server that currently is serving the minimum load (i.e. number of clients) for its region.  The clients will also figure that their server has died when they get errors in connections.  They will then call a reconnect function, which sends a request to the LB to ask “what happened to my server, who should I contact now?”.  The LB will now send these clients the server now tasked for their region, and the clients will continue as normal in their operations.


-------------------------------------------
## Robustness: Password Security

To ensure password security, we store all password information as hashed passwords. We use a randomly generated salt using SHA-256 via hashlib to generate hashed passwords and verify hashes against user-inputted passwords.



-------------------------------------------
## Robustness: Testing

We include both unit tests and integration tests to test all individual methods in isolation as well as entire pipelines of client and server actions. Our tests test for functionalities including the following:
1. Password hashing
2. All client methods
3. Reconnecting if a server fails
4. Replication and heartbeat mechanism
5. Pipeline for creating an account
6. Pipeline for broadcasting a request



-------------------------------------------
## Code Cleanliness

To ensure code cleanliness, we adhered to the following:
1. Simplified and hierarchical code structure, as seen from the earlier section
2. Each file function header has multi-line comments describing its purpose
3. All files generally follow this flow: imports/installs, variables, helper functions, class definitions, and main function.  This flow is enforced by putting comments for each section.






