"""
Test the duration function directly.
"""

import time

from actions.conditional import duration


def test_duration():
    """Test the duration function."""

    print("Testing duration(1.0)...")

    # Create a duration condition for 1 second
    condition = duration(1.0)

    start_time = time.time()

    # Test the condition over time
    for i in range(150):  # 2.5 seconds worth of checks
        current_time = time.time()
        elapsed = current_time - start_time

        result = condition()

        if i % 15 == 0:  # Print every 0.25 seconds
            print(f"Time: {elapsed:.2f}s, condition(): {result}")

        if result:
            print(f"Duration condition returned True at {elapsed:.2f}s")
            break

        time.sleep(0.016)  # Simulate 60 FPS

    print("Test completed")


if __name__ == "__main__":
    test_duration()
