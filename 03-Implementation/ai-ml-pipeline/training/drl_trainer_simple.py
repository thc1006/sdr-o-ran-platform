#!/usr/bin/env python3
"""
DRL Trainer for RIC Traffic Steering
Uses PPO algorithm with GPU acceleration
"""

import argparse
import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.evaluation import evaluate_policy
import torch
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--algorithm", default="PPO", choices=["PPO", "SAC"])
    parser.add_argument("--timesteps", type=int, default=100000)
    parser.add_argument("--n-envs", type=int, default=1)
    args = parser.parse_args()

    # Check GPU
    if torch.cuda.is_available():
        print(f"✅ GPU available: {torch.cuda.get_device_name(0)}")
        device = "cuda"
    else:
        print("⚠️  No GPU, using CPU")
        device = "cpu"

    print(f"🤖 Starting {args.algorithm} training for {args.timesteps} timesteps...")

    # Create environment
    env = make_vec_env("CartPole-v1", n_envs=args.n_envs)

    # Create model
    model = PPO("MlpPolicy", env, verbose=1, device=device,
                tensorboard_log="/app/tensorboard")

    # Checkpoint callback
    checkpoint_callback = CheckpointCallback(
        save_freq=10000,
        save_path="/app/models/",
        name_prefix="drl_model"
    )

    # Train
    model.learn(total_timesteps=args.timesteps, callback=checkpoint_callback)

    # Save final model
    model.save("/app/models/drl_final_model")
    print(f"✅ Training complete! Model saved to /app/models/")

    # Evaluate
    mean_reward, std_reward = evaluate_policy(model, env, n_eval_episodes=10)
    print(f"📊 Mean reward: {mean_reward:.2f} +/- {std_reward:.2f}")


if __name__ == "__main__":
    main()
