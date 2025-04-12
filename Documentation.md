# CS 2620 Final Project

-------------------------------------------
## Design Requirements



-------------------------------------------
## Setup

Clone the repository.
Generate Python gRPC files: Navigate to the root project directory and run `py -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/app.proto`

Run server:
`py -m server.server --pid=PID --host=HOST`
- PID: nonnegative integer, e.g. 0
- HOST: valid host, e.g. 127.0.0.1

ADD INFO ON CONFIG FILES

Run client GUI:
`py -m client.gui`

Run unit tests:
`py -m unittest tests.unit_tests`


-------------------------------------------
## Code Structure




-------------------------------------------
## Assumptions





-------------------------------------------
## GUI Design





-------------------------------------------
## Protocol Design

We utilized gRPC to design how messages were to be sent to/from the client/server.  We encourage you to look into the `chat.proto` file for the complete list of all of our services and messages.  We will highlight the main ones here.



-------------------------------------------
## Server Data: SQL

Format: [COLUMN]: [TYPE], [DEFAULT]

Each server maintains a database with the following tables:

Accounts Table
1. 
   
Broadcasts Table
1. 

Registry Table
1. 

Each load balancer maintains a database with the following tables:

Regions Table:
1. 

Servers Table:
1. 



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






