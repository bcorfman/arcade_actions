CRITICAL: Boundary System Design Principles:
* Apply BoundedMove to individual sprites for simple bouncing behavior
* Apply BoundedMove to sprite lists for coordinated group bouncing (Space Invaders pattern)
* Use WrappedMove for individual sprites or groups for screen wrapping behavior
* Keep boundary detection SIMPLE - track position changes between frames, not complex state management
* Actions move sprites by changing positions directly (NOT change_x/change_y velocities)
* Only check boundaries in the current movement direction (left-moving group only checks left boundary)
* Edge sprite detection: only sprites on the leading edge (leftmost when moving left, rightmost when moving right, etc.)
* Simple callback management: one callback per axis per frame maximum
* NO multiple collision handling, or elaborate state machines
* Direction detection: compare current position to previous position with small threshold (0.1 pixels)