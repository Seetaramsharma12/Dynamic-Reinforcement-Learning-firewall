from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import numpy as np
import logging
from .environment import FirewallEnv
from .agent import FirewallAgent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize global instances
env = FirewallEnv()
agent = FirewallAgent(state_dim=env.observation_space.shape[0], action_dim=env.action_space.n)
is_simulation_running = False

@app.on_event("startup")
async def startup_event():
    global is_simulation_running
    is_simulation_running = True

@app.get("/")
def read_root():
    return {"status": "Firewall AI Agent Running"}

@app.websocket("/ws/traffic")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected to WebSocket")
    
    state = env.reset()
    total_reward = 0
    
    try:
        while True:
            # RL Agent decides action
            # For visualization purpose, we might want to slow it down slightly
            await asyncio.sleep(0.5) 
            
            action = agent.act(state, training=True)
            
            next_state, reward, done, info = env.step(action)
            
            # Train the agent on the fly (Online Learning)
            agent.remember(state, action, reward, next_state, done)
            agent.replay()
            
            if done:
                agent.update_target_network()
                state = env.reset()
            else:
                state = next_state
            
            total_reward += reward
            
            # Prepare data for Frontend
            packet_data = info['packet_details']
            packet_data['action'] = "Block" if action == 1 else "Allow"
            packet_data['reward'] = reward
            packet_data['total_reward'] = total_reward
            packet_data['epsilon'] = agent.epsilon
            
            # Send to UI
            await websocket.send_text(json.dumps(packet_data))
            
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")
