import sys
import os
import torch
import numpy as np

# Resolve paths
base_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(base_dir)
ta_dir = os.path.join(parent_dir, "tugas-akhir")
if ta_dir not in sys.path:
    sys.path.insert(0, ta_dir)

from model_utils import load_models
from src.core.container_env import ContainerEnv
from src.core.candidate_generator import CandidateGenerator

sample_items = [
    {"name": "Boxes 1",  "type": "Box",      "length": 500,  "width": 400,  "height": 300,  "weight": 10.0,  "qty": 80,  "color_idx": 0, "stackable": True},
    {"name": "Sacks",    "type": "Box",      "length": 1000, "width": 450,  "height": 300,  "weight": 45.0,  "qty": 100, "color_idx": 1, "stackable": True},
    {"name": "Big bags", "type": "Box",      "length": 1000, "width": 1000, "height": 1000, "weight": 900.0, "qty": 10,  "color_idx": 3, "stackable": False},
]

# 1. Scale factors
L, W, H = 60, 24, 26
scale_x = 5900 / L
scale_y = 2350 / W
scale_z = 2390 / H

env_items = []
for idx, it in enumerate(sample_items):
    for _ in range(it["qty"]):
        item_l = max(1, int(round(it["length"] / scale_x)))
        item_w = max(1, int(round(it["width"] / scale_y)))
        item_h = max(1, int(round(it["height"] / scale_z)))
        env_items.append({
            'l': item_l,
            'w': item_w,
            'h': item_h,
            'stacking': 'stackable' if it.get("stackable", True) else 'fragile',
            'weight': float(it.get("weight", 10.0)),
            'name': it['name']
        })

ac_model, hl_model = load_models(model_name="no-buffer")

env = ContainerEnv(
    container_length=L,
    container_width=W,
    container_height=H,
    max_items=len(env_items),
    use_structural_validation=False,
    buffer_capacity=3
)

state, action_mask = env.reset()
env.items = env_items

candidate_generator = CandidateGenerator(env.L, env.W)
total_items = len(env.items)
step_count = 0

print(f"Total items in queue: {total_items}")

while env.current_index < total_items and step_count < total_items * 2:
    step_count += 1
    curr_idx = env.current_index
    item_to_place = env.items[curr_idx]
    
    state_tensor = torch.FloatTensor(state).unsqueeze(0)
    with torch.no_grad():
        high_output = hl_model(state_tensor)
        strategy, _ = hl_model.select_strategy(high_output['strategy_logits'], sample=False)
        
    macro_decision = hl_model.decode_macro_decision(strategy)
    orientation = macro_decision.get('orientation', 0)
    
    policy_state, policy_action_mask = env._get_state_and_mask(orientation=orientation)
    
    candidate_actions = candidate_generator.generate_from_macro(
        policy_action_mask,
        macro_decision=macro_decision,
        top_k=128
    )
    
    action = env.L * env.W
    if len(candidate_actions) > 0:
        state_ll_tensor = torch.FloatTensor(policy_state).unsqueeze(0)
        with torch.no_grad():
            logits, _ = ac_model(state_ll_tensor)
            
        env_mask = torch.BoolTensor(np.asarray(policy_action_mask) > 0).unsqueeze(0)
        candidate_mask = torch.zeros_like(env_mask)
        for act in candidate_actions:
            if 0 <= act < env.L * env.W:
                candidate_mask[0, act] = True
                
        combined_mask = env_mask & candidate_mask
        
        if torch.any(combined_mask):
            masked_logits = logits.clone()
            masked_logits[~combined_mask] = float('-inf')
            action = int(torch.argmax(masked_logits).item())
            
    # Step environment
    next_obs, reward, done, info = env.step((action, orientation))
    state = next_obs[0]
    
    action_type = info.get('action_type', 'unknown')
    placed_len = len(env.placed_items)
    
    print(f"Step {step_count}: Item {curr_idx} ({item_to_place['name']}) | Action: {action} | Type: {action_type} | Placed Count: {placed_len} | Buffer Size: {len(env.deferred_buffer)}")
    
    if done:
        print("Environment marked as DONE")
        break

print(f"Final placed items: {len(env.placed_items)}")
