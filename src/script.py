import sys
import threading
import socket
import pickle

ROUTER_PORTS = {}


class Packet:
    def __init__(self, type, data, destination, destination_port, nodes=[]):
        self.type = type
        self.data = data
        self.destination = destination
        self.destination_port = destination_port
        self.nodes = nodes


class Router:
    def __init__(self, isLs, id, G, w, socket):
        self.isLs = isLs
        self.id = id
        self.V, self.E = G
        self.w = w
        self.routing_table = {}
        self.socket = socket

    def bellman_ford(self):
        d = {v: float("inf") for v in self.V}
        d[self.id] = 0

        for _ in range(len(self.V) - 1):
            for (u, v) in self.w:


    def dijkstra(self):
        candidats = set(self.V)
        connections_table = {v: None for v in self.V}

        def c(x, y):
            return self.w[(x, y)]

        def plus_petit():
            v = None
            min_node = float("inf")

            for u in candidats:
                if v is None or connections_table[u][0] < min_node:
                    v = u
                    min_node = connections_table[u][0]

            return v

        for node in self.V:
            if node in self.E[self.id]:
                connections_table[node] = (c(self.id, node), self.id)
            else:
                connections_table[node] = (float("inf"), None)

        suivant = self.id
        while suivant is not None:
            for voisin in self.E[suivant]:
                if voisin in candidats:
                    if connections_table[voisin][0] > connections_table[suivant][0] + c(suivant, voisin):
                        connections_table[voisin] = (connections_table[suivant][0] + c(suivant, voisin), suivant)

            candidats.remove(suivant)
            suivant = plus_petit()

        return connections_table

    def initialize_routing_table(self):
        if self.isLs:
            connections_table = self.dijkstra()

            for v in self.V:
                if v != self.id:
                    current = v
                    next = connections_table[current][1]
                    while connections_table[next][1] is not None:
                        current = next
                        next = connections_table[current][1]

                    self.routing_table[v] = (self.id, current)
        else:
            pass

    def send_to(self, packet, port):
        self.socket.sendto(pickle.dumps(packet), ("127.0.0.1", port))

    def listen(self):
        print(self.id + " Listening on port : " + str(self.socket.getsockname()[1]))
        while True:
            packet, _ = self.socket.recvfrom(65000)
            packet = pickle.loads(packet)
            if packet.type == "data":
                print(self.id + " Received : " + str(packet.data))

                packet.nodes.append(self.id)

                if packet.destination == self.id:
                    print("Router: " + self.id + " is sending the packet to destination host")
                    self.send_to(packet, packet.destination_port)
                else:
                    self.send_to(packet, ROUTER_PORTS[self.routing_table[packet.destination][1]])
            else:
                # Routing table
                pass


class Network:
    def __init__(self, isLs, G, w):
        self.isLs = isLs
        self.G = G
        self.w = w
        self.routers = []
        self.sendHost = None
        self.receiveHost = None

    def listen(self, listener):
        listener.listen()

    def run(self):
        V, E = self.G

        # Create routers and link hosts and start listening thread
        for node in V:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.bind(('127.0.0.1', 0))

            ROUTER_PORTS[node] = s.getsockname()[1]
            router = Router(self.isLs, node, self.G, self.w, s)

            thread = threading.Thread(target=self.listen, args=(router,))
            thread.daemon = True
            thread.start()

            self.routers.append(router)

        # Create receive host and start listening thread
        s_2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s_2.bind(("127.0.0.1", 0))
        self.receiveHost = Host("2", self.routers[-1], s_2)

        thread = threading.Thread(target=self.listen, args=(self.receiveHost,))
        thread.daemon = True
        thread.start()

        # Create sending host
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("127.0.0.1", 0))
        self.sendHost = Host("1", self.routers[0], s)

        if self.isLs:
            for router in self.routers:
                router.initialize_routing_table()
        else:
            pass

        self.sendHost.send("Hello World", self.receiveHost)


class Host:
    def __init__(self, id, router, socket):
        self.id = id
        self.router = router
        self.socket = socket

    def send(self, data, destinationHost):
        packet = Packet("data", str.encode(data), destinationHost.router.id, destinationHost.socket.getsockname()[1])

        # Send data to self.router.
        address = ("127.0.0.1", ROUTER_PORTS[self.router.id])

        print("Host : " + self.id + " is sending data to host : ", destinationHost.id)
        self.socket.sendto(pickle.dumps(packet), address)
        input()

    def listen(self):
        packet, _ = self.socket.recvfrom(65000)
        packet = pickle.loads(packet)
        print("Host has received : " + str(packet.data))
        string = "Packet passed by routers : "
        for node in packet.nodes:
            string += node + " "
        print(string)


def main():
    V = ["a", "b", "c", "d", "e", "f"]
    E = {
        "a": ["b", "d"],
        "b": ["a", "e", "c"],
        "c": ["b", "d", "f"],
        "d": ["a", "c", "e"],
        "e": ["b", "d", "f"],
        "f": ["c", "e"]
    }

    w = {
        ("a", "b"): 5, ("b", "a"): 5,
        ("a", "d"): 45, ("d", "a"): 45,
        ("b", "e"): 3, ("e", "b"): 3,
        ("b", "c"): 70, ("c", "b"): 70,
        ("c", "d"): 50, ("d", "c"): 50,
        ("c", "f"): 78, ("f", "c"): 78,
        ("d", "e"): 8, ("e", "d"): 8,
        ("e", "f"): 7, ("f", "e"): 7
    }

    G = (V, E)
    Network(True if sys.argv[1] == "ls" else False, G, w).run()


if __name__ == "__main__":
    main()
