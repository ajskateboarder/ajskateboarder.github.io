import time
from functools import lru_cache
import logging

import networkx as nx
from pyvis.network import Network
import requests

@lru_cache(maxsize=None)
def get_followers(user):
    followers = []
    offset = 40
    r = requests.get(f"https://api.scratch.mit.edu/users/{user}/followers")
    r.raise_for_status()
    while r.json():
        r = requests.get(
            f"https://api.scratch.mit.edu/users/{user}/followers",
            params={"limit": "40", "offset": offset},
        )
        r.raise_for_status()
        followers.extend(r.json())
        offset += 40
    return followers

@lru_cache(maxsize=None)
def get_some_followers(user, pages):
    followers = []
    offset, page = 40, 1
    r = requests.get(f"https://api.scratch.mit.edu/users/{user}/followers")
    r.raise_for_status()
    while r.json():
        if page >= pages:
            break
        r = requests.get(
            f"https://api.scratch.mit.edu/users/{user}/followers",
            params={"limit": "40", "offset": offset},
        )
        r.raise_for_status()
        followers.extend(r.json())
        offset += 40
        page += 1
    return followers

@lru_cache(maxsize=None)
def get_following(user):
    following = []
    offset = 40
    r = requests.get(f"https://api.scratch.mit.edu/users/{user}/following")
    r.raise_for_status()
    while r.json():
        r = requests.get(
            f"https://api.scratch.mit.edu/users/{user}/following",
            params={"limit": "40", "offset": offset},
        )
        r.raise_for_status()
        following.extend(r.json())
        offset += 40
    return following

def main():
    USERNAME = "griffpatch"
    logging.basicConfig(level=logging.DEBUG)
    G = nx.Graph()

    followers = get_some_followers(USERNAME, 2)

    edges = [
        (USERNAME, user)
        for follower in followers
        if (user := follower["username"])
        if user != USERNAME
    ]

    G.add_edges_from(edges, color="red")

    for _ in range(1):
        for _, username in edges:
            followers = get_some_followers(username, 2)
            edges = [
                (username, user)
                for follower in followers
                if (user := follower["username"])
                if user != username
            ]
            G.add_edges_from(edges)
            time.sleep(0.4)

    print(G.edges)
    nt = Network()
    nt.from_nx(G, show_edge_weights=False)
    nt.save_graph("nx.html")

if __name__ == "__main__":
    main()
