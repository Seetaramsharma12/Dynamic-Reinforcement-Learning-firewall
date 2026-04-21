import gym
from gym import spaces
import numpy as np
import pandas as pd
import random

# Constants for Packet Features
PROTOCOLS = {0: 'TCP', 1: 'UDP', 2: 'ICMP'}
FLAGS = {0: 'SYN', 1: 'ACK', 2: 'FIN', 3: 'RST', 4: 'None'}

class FirewallEnv(gym.Env):
    """
    Custom Environment that follows gym interface.
    Simulates network traffic for the firewall agent to learn.
    """
    metadata = {'render.modes': ['human']}

    def __init__(self):
        super(FirewallEnv, self).__init__()
        
        # Action space: 0 = Allow, 1 = Block
        self.action_space = spaces.Discrete(2)
        
        # Observation space: 
        # [Source IP (int), Dest IP (int), Protocol (0-2), Flag (0-4), Packet Size (norm), Malicious (0/1 - hidden from agent in real scenario but used for reward)]
        # For simplicity in this v1, we'll provide normalized features.
        # 0: Src IP Octet 1 (0-255) / 255
        # 1: Dst IP Octet 1 (0-255) / 255
        # 2: Protocol (0-2) / 2
        # 3: Flag (0-4) / 4
        # 4: Size (0-1500) / 1500
        # 5: Rate of connection (packets per second)
        
        self.observation_space = spaces.Box(low=0, high=1, shape=(6,), dtype=np.float32)
        
        self.state = None
        self.current_packet = None
        self.steps_count = 0
        self.max_steps = 1000

    def reset(self):
        self.steps_count = 0
        self.current_packet = self._generate_packet()
        self.state = self._extract_features(self.current_packet)
        return self.state

    def step(self, action):
        self.steps_count += 1
        
        # Reward Engineering
        # If Malicious (is_malicious=True):
        #   Action 1 (Block) -> +10
        #   Action 0 (Allow) -> -10
        # If Benign (is_malicious=False):
        #   Action 1 (Block) -> -5 (False Positive)
        #   Action 0 (Allow) -> +5
        
        is_malicious = self.current_packet['is_malicious']
        reward = 0
        
        if is_malicious:
            if action == 1:
                reward = 10
            else:
                reward = -10
        else:
            if action == 1:
                reward = -5
            else:
                reward = 5
                
        done = self.steps_count >= self.max_steps
        
        # Generate next packet
        self.current_packet = self._generate_packet()
        self.state = self._extract_features(self.current_packet)
        
        info = {
            'is_malicious': is_malicious,
            'packet_details': self.current_packet
        }
        
        return self.state, reward, done, info

    def render(self, mode='human'):
        print(f"Packet: {self.current_packet}, Action taken: ?")

    def _generate_packet(self):
        # simple heuristic for generation
        # Malicious traffic: often high frequency, specific ports, or specific flags (like SYN flood)
        is_malicious = random.random() < 0.2 # 20% malicious traffic
        
        if is_malicious:
            # Simulate attack pattern (e.g., DDoS or Port Scan)
            protocol = random.choice([0, 1]) # TCP/UDP
            flag = 0 # SYN flood
            size = random.randint(64, 128) # small packets
            rate = random.uniform(0.8, 1.0) # high rate
        else:
            # Normal traffic
            protocol = random.choice([0, 1, 2])
            flag = random.choice([1, 2, 4]) # ACK, FIN, None
            size = random.randint(64, 1500)
            rate = random.uniform(0.0, 0.5)
            
        return {
            'src_ip': f"192.168.1.{random.randint(1, 255)}",
            'dst_ip': f"10.0.0.{random.randint(1, 10)}",
            'protocol': protocol,
            'flag': flag,
            'size': size,
            'rate': rate,
            'is_malicious': is_malicious
        }

    def _extract_features(self, packet):
        # Normalize features
        # Just taking the last octet of IP for simplicity in this vector
        src_octet = int(packet['src_ip'].split('.')[-1]) / 255.0
        dst_octet = int(packet['dst_ip'].split('.')[-1]) / 255.0
        proto_norm = packet['protocol'] / 2.0
        flag_norm = packet['flag'] / 4.0
        size_norm = packet['size'] / 1500.0
        rate = packet['rate']
        
        return np.array([src_octet, dst_octet, proto_norm, flag_norm, size_norm, rate], dtype=np.float32)
