import math
from typing import List
from .interfaces import IScheduler, SDRNode

class BanditScheduler(IScheduler):
    def __init__(self, nodes: List[SDRNode]):
        self.nodes = {f"{n.host}:{n.port}": n for n in nodes}
        # Parameter C for UCB. Higher = more exploration
        self.exploration_factor = 1.0 

    def get_best_node(self) -> SDRNode:
        """Uses Upper Confidence Bound (UCB1) algorithm"""
        if not self.nodes:
            raise ValueError("No nodes available to schedule.")
            
        total_visits = sum(n.visits for n in self.nodes.values())
        
        best_node = None
        best_ucb = -1.0
        
        for node in self.nodes.values():
            # Always explore unvisited nodes first
            if node.visits == 0:
                return node 
                
            # UCB1 formula: Average Reward + C * sqrt(ln(N) / n)
            exploitation = node.score
            exploration = self.exploration_factor * math.sqrt(math.log(total_visits) / node.visits)
            
            ucb = exploitation + exploration
            if ucb > best_ucb:
                best_ucb = ucb
                best_node = node
                
        return best_node

    def update_node_score(self, host: str, port: int, reward: float) -> None:
        """Update using exponential moving average (EMA) to handle non-stationary HF conditions"""
        key = f"{host}:{port}"
        if key in self.nodes:
            node = self.nodes[key]
            alpha = 0.2 # Learning rate
            if node.visits == 0:
                node.score = reward
            else:
                node.score = (1 - alpha) * node.score + alpha * reward
            node.visits += 1
