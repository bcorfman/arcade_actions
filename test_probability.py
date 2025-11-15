"""Test the probability calculation"""

import random

# Simulate the exact logic from allow_enemies_to_fire
num_enemies = 35
chance = 4 + num_enemies * 4  # 144

print(f"Enemies: {num_enemies}")
print(f"Chance: {chance}")
print(f"Probability per enemy: 1/{chance} = {1 / chance:.6f}")
print(f"Expected bullets per call: {num_enemies / chance:.3f}\n")

# Test with seed 42
random.seed(42)
bullets_fired = 0
x_spawn = []

# Simulate one call
for i in range(num_enemies):
    enemy_x = i * 10  # Dummy x positions
    roll = random.randrange(chance)
    if roll == 0 and enemy_x not in x_spawn:
        bullets_fired += 1
        x_spawn.append(enemy_x)
        print(f"Enemy {i} fired! (roll={roll})")

print(f"\nBullets fired in one call: {bullets_fired}")

# Test multiple calls
print("\nTesting 10 calls with seed 42:")
random.seed(42)
total = 0
for call in range(10):
    bullets_this_call = 0
    x_spawn = []
    for i in range(num_enemies):
        enemy_x = i * 10
        roll = random.randrange(chance)
        if roll == 0 and enemy_x not in x_spawn:
            bullets_this_call += 1
            x_spawn.append(enemy_x)
    total += bullets_this_call
    if bullets_this_call > 0:
        print(f"Call {call}: {bullets_this_call} bullets")

print(f"\nTotal bullets in 10 calls: {total}")
