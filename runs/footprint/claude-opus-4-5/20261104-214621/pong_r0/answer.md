# Analysis of Network Weights

## Observations

**Channel 0 (Agent):**
Strong signal exclusively in column 1 (left edge of playable area):
- Row 2 col 1: **1.03** (highest)
- Row 1 col 1: **0.88**
- Row 7 col 1: **0.77**
- Row 6 col 1: **0.67**
- All other interior cells: ~0.04-0.06 (baseline)

The agent appears restricted to column 1, moving only up/down.

**Channel 1 (Moving Objects):**
High values throughout columns 2-8, with a gradient - stronger near the agent:
- Column 2-3 peaks: **1.71**, **1.89**, **1.57**, **1.45**
- Column 7-8 lower: **0.45**, **0.38**, **0.33**, **0.24**
- Column 1 (agent column): all ~0.05-0.07 (baseline)

Moving objects fill the playable area except where the agent is, with proximity to the agent being more important.

**Channel 2 (Reward Targets):**
Very weak overall, but slightly elevated at column 9 (right edge):
- Column 9, rows 1-8: **0.10-0.14** (about 2× baseline)
- All other cells: ~0.04-0.07

Suggests reward is associated with the right edge of the grid.

**Channel 4 (Previous Frame):**
High values throughout interior (rows 1-8, cols 2-8), with peaks like **2.19** at (8,5) and **1.48** at (1,5). This indicates strong reliance on tracking object movement/velocity.

**Channel 3 (Obstacles):**
Only elevated on the wall border (~0.10-0.13), interior is baseline (~0.04-0.06). No interior obstacles.

## Reasoning

- Agent confined to column 1 (only moves up/down) → rules out crossing games like Freeway/Frogger
- Moving objects important throughout the field with proximity gradient → ball or projectile tracking
- Previous frame heavily weighted → velocity/trajectory prediction matters
- Reward signal at right edge → scoring when object reaches the right side
- No interior obstacles → open playfield

This pattern matches a **paddle-and-ball game**: the agent is a paddle on the left side, a ball moves through the playable area, and reward comes when the ball passes the opponent's side (right).

## Game

**Pong**

## Description

The agent controls a paddle on the left edge of the screen, moving up or down to intercept a ball that bounces around the playable area. Reward is earned when the ball passes the opponent's side (right edge).

## Confidence

72%