CRITICAL API Rule - Velocity Semantics:
* ALL velocity values use Arcade's native "pixels per frame at 60 FPS" semantics, NOT "pixels per second"
* MoveUntil((5, 0), condition) means 5 pixels per frame, not 5 pixels per second
* RotateUntil(3, condition) means 3 degrees per frame, not 3 degrees per second  
* This maintains perfect consistency with Arcade's sprite.change_x/change_y/change_angle system
* NEVER convert velocities by dividing/multiplying by frame rates - use raw values directly
* When in doubt about velocity values, refer to Arcade's native sprite velocity documentation
* NEVER use sprite.velocity - that's not how MoveUntil works

CRITICAL: infinite() function rule:
* NEVER suggest changing the infinite() function implementation in actions/frame_conditions.py
* The current implementation (return False) is intentional and correct for the project's usage patterns
* Do not recommend changing it to return lambda: False or any other callable
* This function works correctly with the existing codebase and should not be modified

Arcade 3.x API Guidelines:
* Always prefer the modern Arcade 3.x API
* Text rendering: Use arcade.Text objects that are created once (e.g. in __init__) and drawn with .draw()
* Avoid arcade.draw_text in the render loop - it incurs a high per-frame CPU cost and triggers performance warnings
