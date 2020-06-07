import threading
import socket
import pickle
import datetime
import time

ROUTER_PORTS = {}

class Packet:
    def __init__(self, type_data, data, dest, dest_port, nodes=[]):
        self.type_data = type_data
        self.data = data
        self.dest = dest
        self.dest_port = dest_port
        self.nodes = nodes

class Router:
    def __init__(self, id, socket, graph, weights):
        self.id = id
        self.socket = socket
        self.graph = graph
        self.weights = weights
        self.routing_table = {}
        self.last_updated = None

    def notify_neighbors(self):
        _, E = self.graph

        for node in E[self.id]:
            packet = Packet("routing_table", self.routing_table, node, ROUTER_PORTS[node], nodes=[self.id])
            self.send_to(packet, ROUTER_PORTS[node])


    def update_routing_table(self, received_routing_table, router_id):
        V, _ = self.graph

        new_routing_table = {}

        for v in V:
            if v != self.id:
                if self.weights[(self.id, router_id)] + received_routing_table[v][0] < self.routing_table[v][0]:
                    new_routing_table[v] = (self.weights[(self.id, router_id)] + received_routing_table[v][0], router_id) 
                else:
                    new_routing_table[v] = self.routing_table[v]
            else:
                new_routing_table[self.id] = (0, self.id)

        if new_routing_table != self.routing_table:
            self.last_updated = datetime.datetime.now().time()
            self.routing_table = new_routing_table
            # Envoyer la table de routage à tout ces voisins

            self.notify_neighbors()


    def initialize_routing_table(self):
        V, E = self.graph

        self.routing_table = {v: (self.weights[(self.id, v)], v) if v in E[self.id] else (float("inf"), v) for v in V}
        self.routing_table[self.id] = (0, self.id)

    def listen(self):
        print("Le routeur " + self.id + " est prêt à recevoir")

        while True:
            packet, address = self.socket.recvfrom(65000)
            packet = pickle.loads(packet)

            # Recevoir une table de routage
            if packet.type_data == "routing_table":
                print("Table de routage reçu !") 
                self.update_routing_table(packet.data, packet.nodes[0])
            # Recevoir des datas
            else:
                packet.nodes.append(self.id)

                if packet.dest == self.id:
                    # Envoyer à l'host
                    self.send_to(packet, packet.dest_port)
                else:
                    # Envoyer à un autre routeur
                    self.send_to(packet, ROUTER_PORTS[self.routing_table[packet.dest][1]])
                    # TODO : Véfirier les routeur innactif. (Selon last_updated)

    def send_to(self, packet, port):
        self.socket.sendto(pickle.dumps(packet), ("127.0.0.1", port))


class Host:
    def __init__(self, id, socket, router):
        self.id = id
        self.socket = socket
        self.router = router

    def send_to(self, data, host):
        packet = Packet("data", str.encode(data), host.router.id, host.socket.getsockname()[1])

        # Envoyé le data au routeur connecté
        address = ("127.0.0.1", ROUTER_PORTS[self.router.id])

        print("Le host " + self.id + " à envoyé le data au routeur " + self.router.id) 
        self.socket.sendto(pickle.dumps(packet), address)

    def listen(self):
        print("L'hôte 2 écoute...")
        packet, _ = self.socket.recvfrom(65000)
        packet = pickle.loads(packet)

        print("L'hôte " + self.id + " à reçu : " + str(packet.data))

        string = "Passé par les routeurs : "
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
        ("a", "b"): 5,  ("b", "a"): 5,
        ("a", "d"): 45, ("d", "a"): 45,
        ("b", "e"): 3,  ("e", "b"): 3,
        ("b", "c"): 70, ("c", "b"): 70,
        ("c", "d"): 50, ("d", "c"): 50,
        ("c", "f"): 78, ("f", "c"): 78,
        ("d", "e"): 8,  ("e", "d"): 8,
        ("e", "f"): 7,  ("f", "e"): 7
    }

    routers = []

    for node in V:
        # Créer un routeur ainsi que deux threads
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("127.0.0.1", 0))
        
        ROUTER_PORTS[node] = sock.getsockname()[1]

        router = Router(node, sock, (V, E), w)
        routers.append(router)

        # Création du thread d'écoute
        listen_thread = threading.Thread(target=router.listen)
        listen_thread.start()

    # Créer l'hôte d'envoie
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 0))
    
    send_host = Host("1", sock, routers[0])

    # Créer l'hôte d'écoute
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 0))
    
    receive_host = Host("2", sock, routers[-1])

    # Initialisation des tables de routage
    for router in routers:
        router.initialize_routing_table()

    # Débuter le partage de table de routage
    for router in routers:
        router.notify_neighbors()

    # Partir l'hôte d'écoute
    thread = threading.Thread(target=receive_host.listen)
    thread.start()

    # Attendre que les tables de routage sont correct.

    # Envoie du message
    send_host.send_to("Hello World !", receive_host)


if __name__ == "__main__":
    main()