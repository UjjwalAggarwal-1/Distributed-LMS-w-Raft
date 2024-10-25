import grpc
from concurrent import futures
import threading
import time
import random
import sys, os
import argparse
import base64


sys.path.append(os.path.join(os.path.dirname(__file__), "..", "proto"))

import raft_pb2
import raft_pb2_grpc

from logs_helper import *

# Configurations
HEARTBEAT_INTERVAL = 2  # Seconds
ELECTION_TIMEOUT = 7  # Timeout for starting election


def print_with_time(*args):
    print(f"[{time.time()}] ", *args)


class RaftNode(raft_pb2_grpc.RaftServiceServicer):
    def __init__(self, node_id, port, peers):
        self.node_id = node_id
        self.port = port
        self.peers = peers  # List of other node addresses (IP:Port)
        self.current_term = 0
        self.voted_for = None
        self.state = "follower"
        self.leader_id = None
        self.last_heartbeat = time.time()

        # logs...
        self.log_file = f"logs/{self.node_id}.txt"
        self.log_sync_index = -1  # timestamp is the index, for leader

        with open(self.log_file, "a") as _:
            pass

        # Locks for thread safety, both in server and client
        self.lock = threading.Lock()

        self.current_term = get_last_log_term(self.log_file)
        self.log_sync_index = get_last_log_timestamp(self.log_file)

    def GetLeader(self, request, context):
        leader_address = f"localhost:{self.leader_id+10000}"
        if self.state == "leader":
            leader_address = f"localhost:{self.port+10000}"
        return raft_pb2.GetLeaderResponse(leader_address=leader_address)

    def RedirectWrite(self, request, context):
        try:
            with open(f"logs/{self.port}.txt", "a") as logs:
                logs.write(f"{time.time()} {self.current_term} {request.data}\n")
            return raft_pb2.RedirectWriteResponse(status="success")
        except:
            return raft_pb2.RedirectWriteResponse(status="failure")

    # gRPC server to handle vote requests
    def RequestVote(self, request, context):
        print_with_time(
            f"RequestVote Received, {self.current_term=}, {request.term=}, {request.candidateId=}, {self.voted_for=}"
        )

        with self.lock:
            try:
                # Step 1: If the request term is higher, update current term and become a follower
                if request.term > self.current_term:
                    # self.current_term = (
                    #     request.term - 1
                    # )  # cause i am sure, till -1 of this the request-ing node have seen
                    self.voted_for = None
                    self.state = "follower"

                # Step 2: If the request term is lower, reject the vote
                if request.term <= self.current_term:
                    response = raft_pb2.VoteResponse(
                        voteGranted=False, term=self.current_term
                    )
                    return response

                # Step 3: Check log up-to-date status and grant vote if appropriate
                if (
                    self.voted_for is None or self.voted_for == request.candidateId
                ) and self.is_log_up_to_date(request):
                    self.voted_for = request.candidateId
                    vote_granted = True
                else:
                    vote_granted = False
            except Exception as e:
                print(e)
        try:
            response = raft_pb2.VoteResponse(
                voteGranted=vote_granted, term=self.current_term
            )
        except Exception as e:
            print("excP", e)
        return response

    # Handle AppendEntries RPC (for log replication)
    def AppendEntries(self, request, context):
        print_with_time(
            f"AppendEntries Recvd {self.current_term=}, {request.term=}, {self.leader_id=}, {request.leaderId=}, {request.prevLogIndex}"
        )
        with self.lock:
            try:
                response = raft_pb2.AppendEntriesResponse(
                    success=False, term=self.current_term, missingIndex=-2
                )

                # If the leader's term is higher, update the follower's term
                if request.term > self.current_term:
                    self.current_term = request.term
                    self.state = "follower"
                    self.voted_for = None
                    self.leader_id = request.leaderId

                # Reject the AppendEntries if the term is lower
                if request.term < self.current_term:
                    print("rejected append entries, lower term")
                    return response

                # Check if the follower's logs match the leader's log up to prevLogIndex
                try:
                    last_log_index_ = get_last_log_timestamp(self.log_file)
                except Exception as e:
                    print(e)

                self.last_heartbeat = (
                    time.time()
                )  ## things look good till now, so update heartbeat

                if (
                    request.prevLogIndex != -1
                    and request.prevLogIndex != last_log_index_
                ):
                    # Logs are not in sync; request missing logs from the leader
                    print("rejected append entries, no sync")
                    response.missingIndex = last_log_index_
                    return response

                print("accepted append entries")

                # Append the log entries if they are valid (in sequence)
                print_with_time(f"Appending logs to {self.log_file}")
                decoded_logs = [
                    base64.b64decode(entry).decode("utf-8") for entry in request.entries
                ]
                append_logs_to_file(self.log_file, decoded_logs)

                response.success = True
            except Exception as e:
                print(e)
        return response

    def is_log_up_to_date(self, request):
        # Check if candidate's log is at least as up-to-date as receiver's log
        return True  # Simplified, add actual logic here


# Client-side logic (for sending heartbeats, vote requests, etc.)
class RaftClient:
    def __init__(self, node):
        self.node = node

    def keep_synced(self):
        """
        Leader sends heartbeats to all followers to maintain leadership and replicate logs.
        Followers check if Leader has not been inactive for specified time
        """
        while True:
            if self.node.state == "leader":
                # Leader sends heartbeats to followers
                replication_count = 1
                last_index_, logs_ = find_logs_after_timestamp(
                    self.node.log_file, self.node.log_sync_index
                )
                logs_ = [
                    base64.b64encode(entry.encode("utf-8")).decode("utf-8")
                    for entry in logs_
                ]
                options = [
                    ("grpc.max_send_message_length", 50 * 1024 * 1024),  # e.g., 50 MB
                    ("grpc.max_receive_message_length", 50 * 1024 * 1024),
                ]

                for peer in self.node.peers:
                    with grpc.insecure_channel(peer, options=options) as channel:
                        stub = raft_pb2_grpc.RaftServiceStub(channel)

                        with self.node.lock:
                            # print(
                            #     f"{self.node.current_term=}, {type(self.node.current_term)=}"
                            # )
                            # print(f"{self.node.node_id=}, {type(self.node.node_id)=}")
                            # print(
                            #     f"{self.node.log_sync_index=}, {type(self.node.log_sync_index)=}"
                            # )
                            # print(f"{logs_=}, {type(logs_)=}")
                            request = raft_pb2.AppendEntriesRequest(
                                term=self.node.current_term,
                                leaderId=self.node.node_id,
                                prevLogIndex=float(self.node.log_sync_index),
                                # prevLogTerm=last_term_,
                                entries=logs_,
                                # leaderCommit=self.commitIndex
                            )
                        try:
                            response = stub.AppendEntries(request)
                            if not response.success:
                                if response.missingIndex == -2:
                                    print_with_time(f"Stepping down as leader")
                                    with self.node.lock:
                                        self.node.state = "follower"
                                        return
                                print_with_time(
                                    f"{peer} did not sync logs successfully"
                                )
                                self.handle_log_sync(peer, response.missingIndex)
                            else:
                                replication_count += 1
                        except grpc.RpcError as e:
                            print_with_time(
                                f">>Failed to send heartbeat to node {peer}:{e}"
                            )

                if replication_count > len(self.node.peers) // 2:
                    print_with_time(
                        f"Logs updated successfully for {replication_count} nodes"
                    )
                    with self.node.lock:
                        self.node.log_sync_index = last_index_

                time.sleep(HEARTBEAT_INTERVAL)

            elif self.node.state == "follower":
                # Follower checks for heartbeat timeout
                time.sleep(1)  # Avoid busy-waiting, keep checking periodically
                with self.node.lock:  # adding this because, it might read it when it is being set, which would be an inconsistent state to be in
                    time_since_last_heartbeat = time.time() - self.node.last_heartbeat
                if time_since_last_heartbeat > ELECTION_TIMEOUT:
                    time.sleep(random.random() * 3)
                    print_with_time(
                        f"Node {self.node.node_id} did not recv heartbeat in time"
                    )
                    self.start_election()

    def start_election(self):
        with self.node.lock:
            # self.node.state = "candidate"
            self.node.current_term += 1
            self.node.voted_for = self.node.node_id
            self.node.leader_id = None
        votes = 1  # Vote for self

        print_with_time(
            f"Node {self.node.node_id} starts election for term {self.node.current_term}"
        )

        for peer in self.node.peers:
            with grpc.insecure_channel(peer) as channel:
                stub = raft_pb2_grpc.RaftServiceStub(channel)
                with self.node.lock:
                    request = raft_pb2.VoteRequest(
                        term=self.node.current_term,
                        candidateId=self.node.node_id,
                        # lastLogTerm=self.node.current_term,
                    )

                try:
                    response = stub.RequestVote(request)
                    if response.voteGranted:
                        votes += 1
                        print_with_time(
                            f"Node {peer} granted vote to {self.node.node_id}"
                        )
                    elif response.term > self.node.current_term:
                        # If the peer's term is higher, step down as a follower
                        # self.node.state = "follower"
                        self.node.current_term = response.term
                        print_with_time(
                            f"Node {self.node.node_id} stepping down, term {response.term} is higher"
                        )
                        return  ###
                    else:
                        print_with_time(
                            f"Node {peer} did not vote for {self.node.node_id}"
                        )
                except grpc.RpcError:
                    print_with_time(f"Failed to contact node {peer} for vote request")

        if votes > len(self.node.peers) // 2:
            with self.node.lock:
                # Ensure we haven't stepped down in the meantime
                if self.node.leader_id is None:
                    self.node.leader_id = self.node.port
                    self.node.state = "leader"
                    print_with_time(
                        f"Node {self.node.node_id} became the leader for term {self.node.current_term}, votes received = {votes}"
                    )
        else:
            # self.node.state = "follower"
            self.node.current_term -= 1
            print_with_time(f"Node {self.node.node_id} failed to win election")

    def handle_log_sync(self, peer, missing_index):
        print_with_time(f"Handle log sync, {peer=}, {missing_index=}")
        try:
            _, logs_ = find_logs_after_timestamp(self.node.log_file, missing_index)
            logs_ = [
                base64.b64encode(entry.encode("utf-8")).decode("utf-8") for entry in logs_
            ]
        except Exception as e:
            print("file exp",e)
        with grpc.insecure_channel(peer) as channel:
            try:
                stub = raft_pb2_grpc.RaftServiceStub(channel)

                request = raft_pb2.AppendEntriesRequest(
                    term=self.node.current_term,
                    leaderId=self.node.node_id,
                    prevLogIndex=-1,
                    # prevLogTerm=last_term_,
                    entries=logs_,
                    # leaderCommit=self.commitIndex
                )
                try:
                    response = stub.AppendEntries(request)
                    if not response.success:
                        print_with_time(
                            f"{peer} did not sync logs successfully",
                            peer,
                            response.missingIndex,
                        )
                except grpc.RpcError as e:
                    print_with_time(f"Failed to send heartbeat to node {peer}: {e}")
            except Exception as e:
                print(e)


# Start the gRPC server and client threads
def start_node(node_id, port, peers):
    node = RaftNode(node_id, port, peers)
    client = RaftClient(node)

    server_thread = threading.Thread(target=run_server, args=(node,))
    client_thread = threading.Thread(target=client.keep_synced)

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
    peers = [
        "localhost:40051", # server -> 50051
        "localhost:40052", # server -> 50052 (+10000)
        "localhost:40053",
    ]  # all nodes including the myself

    parser = argparse.ArgumentParser(
        description="Input Node ID and Port number for node"
    )
    # parser.add_argument('node_id', type=int, help="Node ID")
    parser.add_argument("port_number", type=int, help="Port number")
    args = parser.parse_args()
    port = args.port_number

    if f"localhost:{port}" in peers:
        peers.remove(f"localhost:{port}")
    if f"127.0.0.1:{port}" in peers:
        peers.remove(f"127.0.0.1:{port}")

    # taking node id to be the same as the port for now
    start_node(node_id=port, port=port, peers=peers)
