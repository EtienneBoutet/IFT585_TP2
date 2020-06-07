import sys
import threading
import socket
import pickle

ROUTER_PORTS = {}


class Packet:
    def __init__(self, data, destination, destination_port, nodes=[]):
        self.data = data
        self.destination = destination
        self.destination_port = destination_port
        self.nodes = nodes


class Router:
    def __init__(self, id, G, w, socket):
        self.id = id
        self.V, self.E = G
        self.w = w
        self.socket = socket
        self.routing_table = {}

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
        connections_table = self.dijkstra()

        for v in self.V:
            if v != self.id:
                current = v
                next = connections_table[current][1]
                while connections_table[next][1] is not None:
                    current = next
                    next = connections_table[current][1]

                self.routing_table[v] = (self.id, current)

    def send_to(self, packet, port):
        self.socket.sendto(pickle.dumps(packet), ("127.0.0.1", port))

    def listen(self):
        while True:
            packet, _ = self.socket.recvfrom(65000)
            packet = pickle.loads(packet)

            packet.nodes.append(self.id)

            print("Packet reçu par le routeur " + self.id)

            if packet.destination == self.id:
                self.send_to(packet, packet.destination_port)
            else:
                self.send_to(packet, ROUTER_PORTS[self.routing_table[packet.destination][1]])

class Host:
    def __init__(self, id, socket, router):
        self.id = id
        self.socket = socket
        self.router = router

    def send_to(self, data, host):
        packet = Packet(str.encode(data), host.router.id, host.socket.getsockname()[1])

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

        router = Router(node, (V, E), w, sock)
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

    print("Tout les routeurs sont actifs !")

    print("Table de routages finales des routeurs : ")
    for router in routers:
        print(router.id + " : " + str(router.routing_table)) 

    # Partir l'hôte d'écoute
    thread = threading.Thread(target=receive_host.listen)
    thread.start()

    # Envoie du message
    send_host.send_to("Hello World !", receive_host)

if __name__ == "__main__":
    main()
