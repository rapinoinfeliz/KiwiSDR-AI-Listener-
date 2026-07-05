from src.core.scheduler import BanditScheduler
from src.core.interfaces import SDRNode

def test_scheduler_selects_best():
    nodes = [
        SDRNode(host="a.com", port=8073, name="A"),
        SDRNode(host="b.com", port=8073, name="B")
    ]
    scheduler = BanditScheduler(nodes)
    
    # Penalize node A
    scheduler.update_node_score("a.com", 8073, reward=0.0)
    scheduler.update_node_score("a.com", 8073, reward=0.0)
    
    # Reward node B
    scheduler.update_node_score("b.com", 8073, reward=1.0)
    
    # Node B should be selected due to higher UCB score
    best_node = scheduler.get_best_node()
    assert best_node.host == "b.com", "Scheduler should pick the node with higher reward"
