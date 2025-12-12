---
sidebar_position: 2
title: Chapter 2 - Speaking Python
description: Writing your first ROS 2 node with rclpy
---

# Chapter 2: Speaking Python (rclpy)

## Introduction

In Chapter 1, you learned that **nodes are the neurons** of a robot's nervous system. Now it's time to **write your first neuron**! In this chapter, you'll create a simple ROS 2 node in Python that publishes messages—think of it as teaching a robot to say "Hello, Physical AI!"

By the end of this chapter, you'll be able to:
- Write a production-grade ROS 2 publisher node in Python
- Understand the `rclpy` library (ROS Client Library for Python)
- Follow Object-Oriented Programming (OOP) best practices for nodes
- Run and debug your node in simulation

:::tip Learning Outcome
You'll write a minimal "Hello World" publisher node that demonstrates the core anatomy of any ROS 2 program.
:::

## Prerequisites

- **Hardware**: Standard laptop (Sim Mode, no GPU required)
- **Software**:
  - Ubuntu 22.04 LTS with ROS 2 Humble installed
  - Python 3.10+ (comes with Ubuntu 22.04)
  - Text editor (VS Code, Vim, or Nano)
- **Prior Knowledge**:
  - Chapter 1 completed (understanding of nodes and topics)
  - Basic Python programming (classes, functions)

:::note Hardware Requirements - Sim Mode
This chapter runs entirely on a **standard laptop** in simulation. No Jetson Orin, GPU, or physical robot required. All code executes on your CPU.
:::

## The ROS 2 Python Library: `rclpy`

ROS 2 provides **client libraries** for different programming languages:
- `rclpy`: Python (what we'll use)
- `rclcpp`: C++ (for high-performance robotics)
- `rclnodejs`: Node.js (experimental)

Think of `rclpy` as the **Python SDK for robotics**. It handles:
- Connecting your program to the ROS 2 communication system (DDS)
- Creating publishers, subscribers, services, and timers
- Managing node lifecycle (startup, shutdown, error handling)

## Anatomy of a ROS 2 Node: The OOP Structure

Unlike simple scripts, ROS 2 nodes should follow **Object-Oriented Programming** principles. Here's why:

**Bad Example (Procedural Script)**:
```python
# ❌ Don't do this!
import rclpy
pub = rclpy.create_publisher(...)
while True:
    pub.publish("Hello")
```

**Problems**:
- No error handling (what if ROS 2 shuts down?)
- No resource cleanup (memory leaks!)
- Hard to test and reuse

**Good Example (OOP Node)**:
```python
# ✅ Production-ready pattern
class HelloWorldNode(Node):
    def __init__(self):
        super().__init__('hello_world')
        self.publisher = self.create_publisher(...)

    def publish_message(self):
        # Publishing logic here
        pass
```

**Benefits**:
- Encapsulation: All node logic in one class
- Inheritance: Reuse ROS 2's `Node` base class
- Testability: Easy to mock and unit test

:::info Design Principle: OOP for Nodes
Always inherit from `rclpy.node.Node`. This is the foundation of production robotics code!
:::

## Writing Your First Node: Hello World Publisher

Let's build a node that publishes "Hello, Physical AI!" messages at 1 Hz (once per second).

### Step 1: Create the Node File

Create a new file `hello_world_publisher.py`:

```bash
mkdir -p ~/ros2_ws/src/hello_world
cd ~/ros2_ws/src/hello_world
touch hello_world_publisher.py
chmod +x hello_world_publisher.py
```

### Step 2: The Complete Node Code

**Step 2a: Applying `ros2-coder` skill** (OOP, Type Hinting, Entry Point, Resource Management)

```python
#!/usr/bin/env python3
"""
Hello World Publisher Node
A minimal ROS 2 publisher demonstrating production-grade node structure.

Author: Physical AI Course
License: MIT
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from typing import Optional


class HelloWorldPublisher(Node):
    """
    A simple publisher node that sends greeting messages.

    This node demonstrates:
    - Object-Oriented structure (inherits from Node)
    - Type hints for code clarity
    - Timer-based publishing (non-blocking)
    - Resource management
    """

    def __init__(self) -> None:
        """Initialize the Hello World publisher node."""
        super().__init__('hello_world_publisher')

        # Create a publisher for String messages on the '/greetings' topic
        # Queue size of 10 means we buffer up to 10 messages if subscribers are slow
        self.publisher_: rclpy.publisher.Publisher = self.create_publisher(
            String,
            '/greetings',
            10
        )

        # Create a timer that calls publish_message() every 1.0 seconds
        self.timer_period: float = 1.0  # seconds
        self.timer = self.create_timer(self.timer_period, self.publish_message)

        # Message counter
        self.message_count: int = 0

        self.get_logger().info('Hello World Publisher node started! Publishing at 1 Hz.')

    def publish_message(self) -> None:
        """
        Callback function called by the timer.
        Publishes a greeting message to the /greetings topic.
        """
        msg = String()
        msg.data = f'Hello, Physical AI! (Message #{self.message_count})'

        self.publisher_.publish(msg)
        self.get_logger().info(f'Published: "{msg.data}"')

        self.message_count += 1


def main(args: Optional[list] = None) -> None:
    """
    Entry point for the ROS 2 node.

    Args:
        args: Command-line arguments (optional)
    """
    # Initialize the ROS 2 Python client library
    rclpy.init(args=args)

    # Create the node instance
    node: Optional[HelloWorldPublisher] = None

    try:
        node = HelloWorldPublisher()

        # Spin the node (process callbacks) until shutdown
        # This keeps the program running and calling publish_message() every second
        rclpy.spin(node)

    except KeyboardInterrupt:
        # Graceful shutdown on Ctrl+C
        if node:
            node.get_logger().info('Keyboard interrupt detected. Shutting down...')

    except Exception as e:
        # Catch any other errors
        if node:
            node.get_logger().error(f'Unexpected error: {e}')
        raise

    finally:
        # Always clean up resources, even if an error occurred
        if node:
            node.destroy_node()

        # Shutdown the ROS 2 Python client library
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### Code Breakdown: What's Happening?

Let's analyze the key components:

#### 1. Imports and Type Hints
```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from typing import Optional
```
- `rclpy`: The ROS 2 Python library
- `Node`: Base class for all ROS 2 nodes
- `String`: Message type for text data (from `std_msgs` package)
- `Optional`: Type hint for variables that can be `None`

#### 2. Class Definition (OOP Structure)
```python
class HelloWorldPublisher(Node):
    def __init__(self) -> None:
        super().__init__('hello_world_publisher')
```
- **Inherits from `Node`**: Gets all ROS 2 functionality
- **`super().__init__('hello_world_publisher')`**: Registers node with ROS 2 system

#### 3. Creating a Publisher
```python
self.publisher_ = self.create_publisher(String, '/greetings', 10)
```
- **Topic**: `/greetings` (other nodes can subscribe to this)
- **Message Type**: `String` (simple text messages)
- **Queue Size**: `10` (buffer up to 10 messages if network is slow)

#### 4. Timer-Based Publishing
```python
self.timer = self.create_timer(self.timer_period, self.publish_message)
```
- **Non-blocking**: Uses callbacks instead of `while True` loops
- **Precise timing**: ROS 2 handles scheduling automatically

#### 5. Publishing Messages
```python
msg = String()
msg.data = f'Hello, Physical AI! (Message #{self.message_count})'
self.publisher_.publish(msg)
```
- Create a `String` message object
- Set the `data` field
- Publish to all subscribers on `/greetings`

#### 6. Resource Management (try-except-finally)
```python
try:
    node = HelloWorldPublisher()
    rclpy.spin(node)
except KeyboardInterrupt:
    node.get_logger().info('Shutting down...')
finally:
    node.destroy_node()
    rclpy.shutdown()
```
- **`try`**: Normal operation
- **`except KeyboardInterrupt`**: Handle Ctrl+C gracefully
- **`finally`**: **Always** clean up (prevents memory leaks)

:::caution Production Best Practice
Always use `try-except-finally` blocks in your `main()` function. This prevents resource leaks when nodes crash or are interrupted!
:::

## Running Your Node

### Step 1: Source ROS 2 Environment
```bash
source /opt/ros/humble/setup.bash
```

### Step 2: Run the Node
```bash
python3 hello_world_publisher.py
```

You should see:
```
[INFO] [hello_world_publisher]: Hello World Publisher node started! Publishing at 1 Hz.
[INFO] [hello_world_publisher]: Published: "Hello, Physical AI! (Message #0)"
[INFO] [hello_world_publisher]: Published: "Hello, Physical AI! (Message #1)"
[INFO] [hello_world_publisher]: Published: "Hello, Physical AI! (Message #2)"
...
```

Press **Ctrl+C** to stop. You should see a clean shutdown message.

## Verifying the Topic

In a **new terminal**, check if the `/greetings` topic exists:

```bash
# List all active topics
ros2 topic list

# You should see:
# /greetings
# /parameter_events
# /rosout
```

Listen to the messages:
```bash
ros2 topic echo /greetings
```

You'll see:
```yaml
data: 'Hello, Physical AI! (Message #15)'
---
data: 'Hello, Physical AI! (Message #16)'
---
```

:::tip Debugging Tool
`ros2 topic echo` is your best friend! Use it to inspect any topic's data in real time.
:::

## What Makes This "Production-Grade"?

Compare our code to a typical tutorial example:

| Feature | Tutorial Code | Our Code |
|---------|---------------|----------|
| OOP Structure | ❌ Often procedural | ✅ Inherits from `Node` |
| Type Hints | ❌ Rarely used | ✅ All functions typed |
| Error Handling | ❌ No `try-except` | ✅ Full exception handling |
| Resource Cleanup | ❌ Memory leaks | ✅ `finally` block cleanup |
| Logging | ❌ Uses `print()` | ✅ Uses `get_logger()` |
| Non-blocking | ❌ `while True` loops | ✅ Timer callbacks |

:::info Why This Matters
When you deploy to a **Jetson Orin on a Unitree Go2 robot**, production code prevents crashes that could damage hardware!
:::

## Sim-to-Real: Running on Jetson Orin

The exact same code works on physical hardware:

```bash
# On Jetson Orin (after installing ROS 2 Humble)
scp hello_world_publisher.py unitree@jetson-orin:~/
ssh unitree@jetson-orin
python3 hello_world_publisher.py
```

No changes needed! The publisher will work whether it's on:
- Your laptop (x86_64 CPU)
- Jetson Orin (ARM64 GPU)
- Raspberry Pi (ARM32)

This is the power of ROS 2's **platform independence**.

:::tip Hardware Deployment
In Module 3 (Isaac Sim), you'll learn how to test this node in a physics simulator before deploying to real hardware.
:::

## Common Mistakes and How to Fix Them

### Mistake 1: Forgetting `rclpy.init()`
```python
# ❌ This will crash!
node = HelloWorldPublisher()  # Error: rclpy not initialized
```

**Fix**: Always call `rclpy.init()` before creating nodes.

### Mistake 2: Not Calling `destroy_node()`
```python
# ❌ Memory leak!
node = HelloWorldPublisher()
rclpy.spin(node)
# Node object never destroyed
```

**Fix**: Use the `finally` block as shown in our code.

### Mistake 3: Blocking `__init__()`
```python
# ❌ Don't do this!
def __init__(self):
    super().__init__('node')
    while True:  # Blocks forever!
        self.do_something()
```

**Fix**: Use timers or callbacks. Never block in `__init__()`.

## Summary

In this chapter, you learned:

✅ How to write a **production-grade ROS 2 publisher node** in Python
✅ The **OOP structure**: inherit from `Node`, use type hints
✅ **Timer-based publishing** (non-blocking callbacks)
✅ **Resource management** with `try-except-finally`
✅ How to **verify topics** with `ros2 topic list` and `echo`
✅ The same code runs on **laptops and Jetson Orin** (sim-to-real)

## What's Next?

In **Chapter 3: Topics & Services**, you'll learn the difference between:
- **Topics**: Streaming data (like video feeds)
- **Services**: Request-response (like "open gripper")

You'll write a **subscriber node** that listens to camera images.

## Further Reading

- [rclpy API Documentation](https://docs.ros2.org/latest/api/rclpy/)
- [ROS 2 Python Publishers](https://docs.ros.org/en/humble/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Py-Publisher-And-Subscriber.html)
- [std_msgs Message Types](https://docs.ros2.org/latest/api/std_msgs/)

---

**Next Chapter**: [Chapter 3: Topics & Services (Communication) →](./chapter-3-services-actions.md)
