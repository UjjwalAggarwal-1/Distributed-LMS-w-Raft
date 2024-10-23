import grpc
from concurrent import futures
import threading
import time
import random
import sys, os
import argparse


sys.path.append(os.path.join(os.path.dirname(__file__), "..", "proto"))

import raft_pb2
import raft_pb2_grpc

# Configurations
HEARTBEAT_INTERVAL = 2  # Seconds
ELECTION_TIMEOUT = 5  # Timeout for starting election

def print_with_time(*args):
    print(time.time(), *args)


class RaftNode(raft_pb2_grpc.RaftServiceServicer):
    def __init__(self, node_id, port, peers):
        self.node_id = node_id
        self.port = port
        self.peers = peers  # List of other node addresses (IP:Port)
        self.current_term = 0
        self.voted_for = None
        self.log = []
        self.state = "follower"
        self.leader_id = None
        self.last_heartbeat = time.time()

        # Locks for thread safety
        self.lock = threading.Lock()

    # gRPC server to handle vote requests
    def RequestVote(self, request, context):
        print_with_time("RequestVote", self.term, request.term, request.candidateId, self.voted_for)
        with self.lock:
            response = raft_pb2.VoteResponse()
            if request.term > self.current_term:
                self.current_term = request.term
                self.voted_for = None
                self.state = "follower"

            if (
                self.voted_for is None or self.voted_for == request.candidateId
            ) and self.is_log_up_to_date(request):
                self.voted_for = request.candidateId
                response.voteGranted = True
            else:
                response.voteGranted = False
            response.term = self.current_term
            return response

    # Handle AppendEntries RPC (for log replication)
    def AppendEntries(self, request, context):
        print_with_time("AppendEntries")
        with self.lock:
            response = raft_pb2.AppendResponse(success=False, term=self.current_term)
            # Step down if the term in the request is higher
            if request.term > self.current_term:
                self.current_term = request.term
                self.state = "follower"
                self.voted_for = None
                self.leader_id = request.leaderId
            
            if request.term < self.current_term:
                return response
            
            # If terms match, continue with log replication
            self.leader_id = request.leaderId
            response.success = True
            return response

    # Heartbeat RPC to reset follower's timeout
    def Heartbeat(self, request, context):
        print_with_time("Heartbeat")
        with self.lock:
            response = raft_pb2.HeartbeatResponse(success=False)
            if request.term >= self.current_term:
                self.current_term = request.term
                self.leader_id = request.leaderId
                self.last_heartbeat = time.time()
                response.success = True
            return response

    def is_log_up_to_date(self, request):
        # Check if candidate's log is at least as up-to-date as receiver's log
        return True  # Simplified, add actual logic here


# Client-side logic (for sending heartbeats, vote requests, etc.)
class RaftClient:
    def __init__(self, node):
        self.node = node

    def send_heartbeat(self):
        while True:
            if self.node.state == "leader":
                # Leader sends heartbeats to followers
                for peer in self.node.peers:
                    with grpc.insecure_channel(peer) as channel:
                        stub = raft_pb2_grpc.RaftServiceStub(channel)
                        request = raft_pb2.HeartbeatRequest(term=self.node.current_term, leaderId=self.node.node_id)
                        try:
                            response = stub.Heartbeat(request)
                            if not response.success:
                                print_with_time(f"Failed heartbeat to {peer}, term mismatch.")
                        except grpc.RpcError:
                            print_with_time(f"Failed to contact node {peer}")
                time.sleep(HEARTBEAT_INTERVAL)

            elif self.node.state == "follower":
                # Follower checks for heartbeat timeout
                time_since_last_heartbeat = time.time() - self.node.last_heartbeat
                if time_since_last_heartbeat > ELECTION_TIMEOUT:
                    time.sleep(random.random()*3)
                    print_with_time(f"Node {self.node.node_id} did not receive heartbeat in time. Starting election.")
                    self.start_election()

            time.sleep(1)  # Avoid busy-waiting, keep checking periodically

    def start_election(self):
        self.node.state = "candidate"
        self.node.current_term += 1
        self.node.voted_for = self.node.node_id
        votes = 1  # Vote for self

        print_with_time(f"Node {self.node.node_id} starts election for term {self.node.current_term}")

        for peer in self.node.peers:
            with grpc.insecure_channel(peer) as channel:
                stub = raft_pb2_grpc.RaftServiceStub(channel)
                request = raft_pb2.VoteRequest(term=self.node.current_term, candidateId=self.node.node_id,
                                               lastLogIndex=len(self.node.log), lastLogTerm=self.node.current_term)
                
                try:
                    response = stub.RequestVote(request)
                    if response.voteGranted:
                        votes += 1
                        print_with_time(f"Node {peer} granted vote to {self.node.node_id}")
                    elif response.term > self.node.current_term:
                        # If the peer's term is higher, step down as a follower
                        self.node.state = "follower"
                        self.node.current_term = response.term
                        print_with_time(f"Node {self.node.node_id} stepping down, term {response.term} is higher")
                        return
                except grpc.RpcError:

                    print_with_time(f"Failed to contact node {peer} for vote request")

        if votes > len(self.node.peers) // 2:
            with self.node.lock:
                # Ensure we haven't stepped down in the meantime
                if self.node.state == "candidate":
                    self.node.state = "leader"
                    print_with_time(f"Node {self.node.node_id} became the leader for term {self.node.current_term}")
        else:
            self.node.state = "follower"
            print_with_time(f"Node {self.node.node_id} failed to win election")


# Start the gRPC server and client threads
def start_node(node_id, port, peers):
    node = RaftNode(node_id, port, peers)
    client = RaftClient(node)

    server_thread = threading.Thread(target=run_server, args=(node,))
    client_thread = threading.Thread(target=client.send_heartbeat)

    server_thread.start()
    client_thread.start()

    server_thread.join()
    client_thread.join()


def run_server(node):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    raft_pb2_grpc.add_RaftServiceServicer_to_server(node, server)
    server.add_insecure_port(f"[::]:{node.port}")
    try:
        server.start()
        print_with_time(f"Node {node.node_id} started on port {node.port}")
        server.wait_for_termination()
    except KeyboardInterrupt:
        print_with_time(f"Shutting down server {node.node_id}...")
        server.stop(0)  # Graceful shutdown


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Input Node ID and Port number for node")

    # parser.add_argument('node_id', type=int, help="Node ID")
    parser.add_argument('port_number', type=int, help="Port number")
    args = parser.parse_args()

    peers = ["localhost:40051", "localhost:40052", "localhost:40053"]
    start_node(node_id=args.port_number, port=args.port_number, peers=peers)
