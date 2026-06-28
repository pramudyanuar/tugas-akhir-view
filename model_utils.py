import os
import sys
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

# Resolve paths to allow importing from the 'tugas-akhir' directory
base_dir = os.path.dirname(os.path.abspath(__file__)) # tugas-akhir-view
parent_dir = os.path.dirname(base_dir) # ta
ta_dir = os.path.join(parent_dir, "tugas-akhir")
if ta_dir not in sys.path:
    sys.path.insert(0, ta_dir)

# Import original classes from backend
from src.core.container_env import ContainerEnv
from src.core.candidate_generator import CandidateGenerator
from src.learning.models.high_level_agent import HighLevelAgent
from src.learning.models.actor_critic import ActorCriticNetwork


def load_models(model_name="no-buffer", model_dir=None):
    if model_dir is None or model_dir == "model":
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_dir = os.path.join(base_dir, "model")

    # Load low-level actor-critic model and high-level agent from original classes
    ac_model = ActorCriticNetwork(L=60, W=24, action_size=60*24+1)
    hl_model = HighLevelAgent(input_dim=60*24+4)
    
    norm_name = model_name.replace("-", "_")
    ac_filename = f"{norm_name}_ac.pt"
    hl_filename = f"{norm_name}_hl.pt"
    
    ac_path = os.path.join(model_dir, ac_filename)
    hl_path = os.path.join(model_dir, hl_filename)
    
    if not os.path.exists(ac_path) or not os.path.exists(hl_path):
        ac_path = os.path.join(model_dir, "buffer_3_ac.pt")
        hl_path = os.path.join(model_dir, "buffer_3_hl.pt")
        print(f"[Warning] Model files for '{model_name}' not found. Falling back to buffer_3: {ac_path}")
    else:
        print(f"[Info] Loading model '{model_name}'")
        
    ac_state = torch.load(ac_path, map_location="cpu")
    ac_model.load_state_dict(ac_state)
    ac_model.eval()

    hl_state = torch.load(hl_path, map_location="cpu")
    hl_model.load_state_dict(hl_state)
    hl_model.eval()
    
    return ac_model, hl_model


def pack_hierarchical_drl(items, container_length_mm, container_width_mm, container_height_mm, model_name="no-buffer", progress_callback=None):
    """
    Run hierarchical DRL inference on a list of items using the official ContainerEnv backend.
    """
    # 1. Initialize grid dimensions and scale factors
    L, W, H = 60, 24, 26
    scale_x = container_length_mm / L
    scale_y = container_width_mm / W
    scale_z = container_height_mm / H
    
    # 2. Convert items from mm to grid units
    env_items = []
    for idx, it in enumerate(items):
        item_l = max(1, int(round(it["length"] / scale_x)))
        item_w = max(1, int(round(it["width"] / scale_y)))
        item_h = max(1, int(round(it["height"] / scale_z)))
        
        env_items.append({
            'l': item_l,
            'w': item_w,
            'h': item_h,
            'stacking': 'stackable' if it.get("stackable", True) else 'fragile',
            'weight': float(it.get("weight", 10.0)),
        })
        
    # 3. Load trained neural networks
    ac_model, hl_model = load_models(model_name=model_name)
    
    # Determine buffer capacity based on selected model
    buffer_capacity = 0
    if "buffer-" in model_name:
        try:
            buffer_capacity = int(model_name.split("-")[1])
        except:
            buffer_capacity = 3
            
    # 4. Initialize the official ContainerEnv
    env = ContainerEnv(
        container_length=L,
        container_width=W,
        container_height=H,
        max_items=len(env_items),
        use_structural_validation=False,
        buffer_capacity=buffer_capacity
    )
    
    # Reset environment and manually override the items list
    state, action_mask = env.reset()
    env.items = env_items
    
    candidate_generator = CandidateGenerator(env.L, env.W)
    total_items = len(env.items)
    step_count = 0
    
    print(f"[Dashboard] Starting DRL packing for {total_items} items...", flush=True)
    if progress_callback:
        progress_callback(0, 0)
        
    # Track the state of the buffer at each placement step
    buffer_history = []
    
    # Run the exact evaluation decision loop
    while env.current_index < total_items and step_count < total_items * 2:
        step_count += 1
        old_placed_len = len(env.placed_items)
        
        # High-level decision: select packing strategy
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        with torch.no_grad():
            high_output = hl_model(state_tensor)
            strategy, _ = hl_model.select_strategy(high_output['strategy_logits'], sample=False)
            
        macro_decision = hl_model.decode_macro_decision(strategy)
        orientation = macro_decision.get('orientation', 0)
        
        # Get low-level state and action mask based on the selected orientation
        policy_state, policy_action_mask = env._get_state_and_mask(orientation=orientation)
        
        # Generate candidate coordinates using the CandidateGenerator
        candidate_actions = candidate_generator.generate_from_macro(
            policy_action_mask,
            macro_decision=macro_decision,
            top_k=128
        )
        
        # Low-level decision: choose best coordinate from candidates
        if len(candidate_actions) > 0:
            # Predict logits
            state_ll_tensor = torch.FloatTensor(policy_state).unsqueeze(0)
            with torch.no_grad():
                logits, _ = ac_model(state_ll_tensor)
                
            # Construct masks
            env_mask = torch.BoolTensor(np.asarray(policy_action_mask) > 0).unsqueeze(0)
            candidate_mask = torch.zeros_like(env_mask)
            for act in candidate_actions:
                if 0 <= act < env.L * env.W:
                    candidate_mask[0, act] = True
                    
            combined_mask = env_mask & candidate_mask
            
            if torch.any(combined_mask):
                masked_logits = logits.clone()
                masked_logits[~combined_mask] = float('-inf')
                # Deterministic selection for visual consistency
                action = int(torch.argmax(masked_logits).item())
            else:
                action = env.L * env.W  # Fallback to skip/defer
        else:
            action = env.L * env.W  # Skip/defer
            
        # Step the environment
        next_obs, reward, done, info = env.step((action, orientation))
        state = next_obs[0]
        
        new_placed_len = len(env.placed_items)
        if new_placed_len > old_placed_len:
            # Record the buffer state right after this placement occurred
            # We copy the deferred buffer items
            current_buffer = []
            for bit in env.deferred_buffer:
                current_buffer.append({
                    'l': bit['l'],
                    'w': bit['w'],
                    'h': bit['h'],
                    'weight': bit.get('weight', 10.0),
                    '_orig_idx': bit.get('_orig_idx', 0)
                })
            for _ in range(new_placed_len - old_placed_len):
                buffer_history.append(current_buffer)
        
        if progress_callback:
            progress_callback(env.current_index, len(env.placed_items))
            
        if step_count % 20 == 0 or env.current_index >= total_items:
            print(f"[Dashboard] Packed {env.current_index}/{total_items} items... (Placed: {len(env.placed_items)})", flush=True)
            
    print(f"[Dashboard] DRL packing finished! Total placed: {len(env.placed_items)}", flush=True)
        
    # 5. Map grid placements back to mm coordinates for 3D rendering
    placed = []
    matched_indices = set()
    
    for placed_idx, (grid_x, grid_y, grid_z) in enumerate(env.placed_positions):
        placed_item = env.placed_items[placed_idx]
        pl, pw, ph = placed_item['l'], placed_item['w'], placed_item['h']
        
        # Find the original item that matches these grid dimensions
        found_idx = None
        for idx, env_it in enumerate(env_items):
            if idx in matched_indices:
                continue
            # Match dimensions (taking rotation into account)
            if (env_it['l'] == pl and env_it['w'] == pw and env_it['h'] == ph) or \
               (env_it['w'] == pl and env_it['l'] == pw and env_it['h'] == ph):
                found_idx = idx
                break
                
        if found_idx is not None:
            matched_indices.add(found_idx)
            orig_item = items[found_idx]
            
            # Detect if it was rotated
            item_rotated = (pl == env_items[found_idx]['w'] and pw == env_items[found_idx]['l'])
            
            # Scale coordinates back to mm (inverting Y-axis so packing starts at the back wall)
            pos_x_mm = container_length_mm - (grid_x + pl) * scale_x # Length position (Y-axis in 3D viz)
            pos_y_mm = grid_y * scale_y # Width position (X-axis in 3D viz)
            pos_z_mm = grid_z * scale_z # Height position (Z-axis in 3D viz)
            
            if item_rotated:
                l_mm = orig_item["width"]
                w_mm = orig_item["length"]
            else:
                l_mm = orig_item["length"]
                w_mm = orig_item["width"]
            h_mm = orig_item["height"]
            
            placed.append({
                **orig_item,
                "length": int(round(l_mm)),
                "width": int(round(w_mm)),
                "height": int(round(h_mm)),
                "pos_x": int(round(pos_y_mm)), # X-axis = Width
                "pos_y": int(round(pos_x_mm)), # Y-axis = Length
                "pos_z": int(round(pos_z_mm)), # Z-axis = Height
                "_flat_idx": orig_item.get("_flat_idx", found_idx),
                "buffer": [
                    {
                        "name": f"Box {bit.get('_orig_idx', 0) + 1}",
                        "length": int(round(bit['l'] * scale_x)),
                        "width": int(round(bit['w'] * scale_y)),
                        "height": int(round(bit['h'] * scale_z)),
                        "color_idx": bit.get('_orig_idx', 0) % 12
                    }
                    for bit in buffer_history[placed_idx]
                ] if placed_idx < len(buffer_history) else []
            })
            
    return placed
