import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.discovery import KiwiSDRDiscoveryService
from src.core.scheduler import BanditScheduler
from src.core.interfaces import SDRNode

def test_scheduler():
    print("Testing Discovery...")
    discovery = KiwiSDRDiscoveryService()
    # Mock some nodes if we don't want to actually ping the public list
    nodes = [
        SDRNode(host="kiwisdr.sk3w.se", port=8073, name="SK3W"),
        SDRNode(host="w3hf.ddns.net", port=8073, name="W3HF"),
        SDRNode(host="kiwi.hackerspace.com", port=8073, name="HackerSpace")
    ]
    
    print("Testing Scheduler (UCB1)...")
    scheduler = BanditScheduler(nodes)
    
    # 1. Should pick first unvisited node
    node1 = scheduler.get_best_node()
    print("Selected:", node1.name)
    scheduler.update_node_score(node1.host, node1.port, reward=0.8) # Good score
    
    # 2. Should pick second unvisited node
    node2 = scheduler.get_best_node()
    print("Selected:", node2.name)
    scheduler.update_node_score(node2.host, node2.port, reward=0.2) # Bad score
    
    # 3. Should pick third unvisited node
    node3 = scheduler.get_best_node()
    print("Selected:", node3.name)
    scheduler.update_node_score(node3.host, node3.port, reward=0.5) # Med score
    
    # 4. Now all are visited (visits=1). Should pick the best one (SK3W) because of exploitation
    # or another one if exploration factor is high enough.
    node4 = scheduler.get_best_node()
    print("Selected after all visited:", node4.name, "Score:", node4.score)
    
    # Feed bad score to best node to see if it drops
    scheduler.update_node_score(node4.host, node4.port, reward=0.1)
    
    # 5. Should pick a different node now
    node5 = scheduler.get_best_node()
    print("Selected after punishment:", node5.name, "Score:", node5.score)

if __name__ == "__main__":
    test_scheduler()
