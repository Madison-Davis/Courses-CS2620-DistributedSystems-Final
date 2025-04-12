# CS 2620 Final Project

-------------------------------------------
## Design Requirements



-------------------------------------------
## Setup

Clone the repository.
Generate Python gRPC files: Navigate to the root project directory and run `py -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/app.proto`

Run server:
`py -m server.server --host=HOST --region=REGION`
- HOST: valid host, e.g. 127.0.0.1
- REGION: integer in {0, 1, 2}

ADD INFO ON CONFIG FILES

Run client GUI:
`py -m client.gui`

Run unit tests:
`py -m unittest tests.unit_tests`


-------------------------------------------
## Code Structure

```
├── client
│   ├── client.py               → AppClient class, functions to request/receive from server
│   ├── gui.py                  → creates GUI for client
├── proto
│   ├── app.proto               → defines gRPC services and messages for requests/responses
│   ├── app_pb2.py              → generated code from compiler: for all .proto service/rpc defs
│   ├── app_pb2_grpc.py         → generated code from compiler: for all .proto message defs
├── config
│   ├── config.py               → defines HOST/PORT and other parameters
├── server
│   ├── server.py               → AppService class, functions to use SQL and return results
│   ├── server_security.py      → for password hashing
├── load_balancer
│   ├── load_balancer.py        → functions for the load balancer
├── tests
│   ├── unit_tests.py           → unit tests
└── Documentation.md
```


-------------------------------------------
## Assumptions





-------------------------------------------
## GUI Design





-------------------------------------------
## Protocol Design

We utilized gRPC to design how messages were to be sent to/from the client/server.  We encourage you to look into the `app.proto` file for the complete list of all of our services and messages.  We will highlight the main ones here.



-------------------------------------------
## Server Data: SQL

Format: [COLUMN]: [TYPE]

Each server maintains a database with the following tables:

Accounts Table
1. uuid: integer primary key autoincrement
2. username: text
3. region: integer in {0, 1, 2}
4. dogs: integer
5. capacity: integer
6. pwd_hash: text
   
Broadcasts Table
1. broadcast_id: integer primary key autoincrement
2. recipient_id: integer
3. sender_id: integer
4. amount_requested: integer
5. status: integer in {0, 1, 2}

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



-------------------------------------------
## Robustness: Password Security

To ensure password security, we store all password information as hashed passwords. We use a randomly generated salt using SHA-256 via hashlib to generate hashed passwords and verify hashes against user-inputted passwords.



-------------------------------------------
## Robustness: Testing

Our unit tests test for functionalities including the following:
1. 



-------------------------------------------
## Code Cleanliness

To ensure code cleanliness, we adhered to the code structure as articulated in an earlier section.  We also did the following:
1. 






