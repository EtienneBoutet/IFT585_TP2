import sys

class Router:
    def __init__(self, id , G, w):
        self.id = id
        self.V, self.E = G
        self.w = w
        self.routing_table = {}

    def dijkstra(self):
        candidats = set(self.V)
        connections_table = {v: None for v in self.V}

        def c(x,y):
            return self.w[(x, y)]

        def plus_petit():
            v = None
            min_node = float("inf")
            
            for u in candidats:
                if v is None or connections_table[u][0] < min_node:
                    v = u 

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

    def update_routing_table(self):
        connections_table = self.dijkstra()

        for v in self.V:
            if v != self.id:
                current = v
                next = connections_table[current][1]
                while connections_table[next][1] is not None:
                    current = next
                    next = connections_table[current][1]
                
                self.routing_table[v] = (self.id, current)

class Network:
    def __init__(self, isLs, G, w, sendHost, receiveHost):
        self.isLs = isLs
        # Graph
        self.G = G
        # weights
        self.w = w
        self.routers = []
        self.sendHost = sendHost
        self.receiveHost = receiveHost

    def create_routers_and_link_hosts(self):
        V, E = self.G
        for node in V:
            self.routers.append(Router(node, self.G, self.w))

        self.sendHost.router = self.routers[0]
        self.receiveHost.router = self.routers[-1]


class Host:
    def __init__(self):
        router = None


def main():
    # isLs = sys.argv[1] 
    sendHost = Host()
    receiveHost = Host()

    V = ["a", "b", "c", "d",  "e", "f"]
    E = {
        "a" : ["b", "d"],
        "b" : ["a", "e", "c"],
        "c" : ["b", "d", "f"],
        "d" : ["a", "c", "e"],
        "e" : ["b", "d", "f"],
        "f" : ["c", "e"]
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

    G = (V, E)
    Network(True, G, w, sendHost, receiveHost).create_routers_and_link_hosts()



if __name__ == "__main__":
    main()