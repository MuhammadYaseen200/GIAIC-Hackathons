---
sidebar_position: 3
title: Chapter 3 - Topics & Services
description: Understanding communication patterns in ROS 2
---

# Chapter 3: Topics & Services (Communication)

## Introduction

In Chapter 2, you learned how to **publish messages** on a topic. But how do other nodes receive that data? And what if you need a **request-response** pattern instead of continuous streaming?

In this chapter, you'll learn the two fundamental communication patterns in ROS 2:
- **Topics**: Continuous data streams (like video feeds from a camera)
- **Services**: Request-response calls (like "Open the gripper now!")

By the end of this chapter, you'll understand when to use each pattern and write a **subscriber node** that listens to camera images.

:::tip Learning Outcome
You'll write a subscriber node that listens to `/camera/image_raw` and understand the difference between topics (streaming) and services (RPC calls).
:::

## Prerequisites

- **Hardware**: Standard laptop (Sim Mode, no GPU required)
- **Software**:
  - Ubuntu 22.04 LTS with ROS 2 Humble
  - Python 3.10+
  - `ros2` command-line tools
- **Prior Knowledge**:
  - Chapters 1-2 completed (nodes, publishers)
  - Basic understanding of asynchronous programming

:::note Hardware Requirements - Sim Mode
This chapter runs entirely on a **standard laptop** using simulated camera data. No physical RealSense camera, Jetson Orin, or GPU required.
:::

## The Two Communication Paradigms

Imagine you're building a robot assistant in a kitchen. It needs two types of communication:

### Scenario 1: Monitoring (Continuous Streaming)
**Problem**: "Keep watching the stove. If you see smoke, alert me immediately."

This requires **continuous data flow**:
- Camera publishes images at 30 FPS (frames per second)
- Smoke detector node subscribes to every frame
- Data flows **one-way** (camera → detector)

→ **Use a TOPIC**

### Scenario 2: Commands (Request-Response)
**Problem**: "Open the fridge door when I say so."

This requires **on-demand action**:
- You send a command: "Open fridge"
- Gripper node responds: "Done" or "Failed: door stuck"
- Communication is **two-way** (request → response)

→ **Use a SERVICE**

![Diagram: Topics vs Services Communication Patterns](../../static/img/module1/topics-vs-services.png)

## Topics: Publish-Subscribe Pattern

Topics use the **publish-subscribe (pub-sub)** pattern:

```
┌───────────┐    /camera/image_raw    ┌──────────────┐
│  Camera   │───────────────────────▶│  Detector    │
│  Node     │    (30 FPS stream)      │  Node        │
└───────────┘                         └──────────────┘
                                             │
                                             ▼
                                      ┌──────────────┐
                                      │  Logger      │
                                      │  Node        │
                                      └──────────────┘
```

**Key Properties**:
- **One-to-many**: One publisher, multiple subscribers
- **Decoupled**: Publisher doesn't know who subscribes
- **Continuous**: Data flows at publisher's rate (e.g., 30 Hz)
- **Asynchronous**: Subscribers process messages independently

### When to Use Topics

Use topics for:
- **Sensor data**: Camera images, lidar scans, IMU readings
- **State updates**: Robot position, battery level, temperature
- **Telemetry**: Logging, diagnostics, monitoring

:::info Topic Naming Convention
Topic names start with `/` and use lowercase with underscores:
- ✅ `/camera/image_raw`
- ✅ `/robot/battery_voltage`
- ❌ `/CameraImage` (avoid camelCase)
:::

## Services: Request-Response Pattern

Services use the **client-server (RPC)** pattern:

```
┌───────────┐                         ┌──────────────┐
│  Planner  │──── "Open gripper" ────▶│  Gripper     │
│  Node     │                          │  Node        │
│ (Client)  │◀─── "Success!" ─────────│  (Server)    │
└───────────┘                         └──────────────┘
```

**Key Properties**:
- **One-to-one**: One client, one server per call
- **Synchronous**: Client waits for response (blocking)
- **On-demand**: Only executed when requested
- **Stateful**: Can return success/failure codes

### When to Use Services

Use services for:
- **Actuator commands**: "Open gripper", "Move arm to position X"
- **Configuration**: "Set camera exposure to 50ms"
- **Queries**: "What's the current map size?"

:::caution Blocking Behavior
Service calls **block the client** until the server responds. For long-running tasks (>1 second), use **Actions** instead (covered in advanced topics).
:::

## Writing a Subscriber Node: Camera Image Listener

Let's write a node that subscribes to `/camera/image_raw` (simulated camera data).

### The Image Message Type

ROS 2 uses standardized message types from the `sensor_msgs` package:

```python
from sensor_msgs.msg import Image

# Image message contains:
# - header (timestamp, frame_id)
# - height, width (pixels)
# - encoding (e.g., "rgb8", "bgr8")
# - data (raw pixel array)
```

### Complete Subscriber Code

**Step 2a: Applying `ros2-coder` skill** (OOP, Type Hints, Resource Management)

```python
#!/usr/bin/env python3
"""
Camera Image Subscriber Node
Demonstrates subscribing to streaming image data from a camera topic.

Author: Physical AI Course
License: MIT
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from typing import Optional


class CameraSubscriber(Node):
    """
    A subscriber node that listens to camera image streams.

    This node demonstrates:
    - Subscribing to high-frequency topics (camera data)
    - Processing callback functions
    - Handling image message types
    """

    def __init__(self) -> None:
        """Initialize the camera subscriber node."""
        super().__init__('camera_subscriber')

        # Create a subscription to the /camera/image_raw topic
        # Queue size of 10 means we buffer up to 10 images if processing is slow
        self.subscription = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )

        # Counter for received images
        self.frame_count: int = 0

        self.get_logger().info('Camera Subscriber node started. Listening to /camera/image_raw')

    def image_callback(self, msg: Image) -> None:
        """
        Callback function executed whenever a new image is published.

        Args:
            msg: Image message containing camera data
        """
        self.frame_count += 1

        # Extract image metadata
        height: int = msg.height
        width: int = msg.width
        encoding: str = msg.encoding
        timestamp_sec: int = msg.header.stamp.sec
        timestamp_nanosec: int = msg.header.stamp.nanosec

        # Log every 30th frame to avoid spamming the console (at 30 FPS = once per second)
        if self.frame_count % 30 == 0:
            self.get_logger().info(
                f'Received frame #{self.frame_count}: '
                f'{width}x{height} pixels, encoding={encoding}, '
                f'timestamp={timestamp_sec}.{timestamp_nanosec}'
            )

        # In a real application, you would process the image here:
        # - Run object detection (YOLO, MobileNet)
        # - Perform SLAM (Simultaneous Localization and Mapping)
        # - Extract features for visual servoing


def main(args: Optional[list] = None) -> None:
    """
    Entry point for the ROS 2 node.

    Args:
        args: Command-line arguments (optional)
    """
    # Initialize the ROS 2 Python client library
    rclpy.init(args=args)

    # Create the node instance
    node: Optional[CameraSubscriber] = None

    try:
        node = CameraSubscriber()

        # Spin the node (process callbacks) until shutdown
        # This keeps the program running and calling image_callback() for each new image
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
        # Always clean up resources
        if node:
            node.destroy_node()

        # Shutdown the ROS 2 Python client library
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### Code Breakdown

#### 1. Creating a Subscription
```python
self.subscription = self.create_subscription(
    Image,              # Message type
    '/camera/image_raw', # Topic name
    self.image_callback, # Callback function
    10                   # Queue size
)
```

**Key differences from publisher**:
- No `create_publisher()`, we use `create_subscription()`
- Must provide a **callback function** (called for each message)
- **Queue size**: Buffer for messages arriving faster than we can process

#### 2. The Callback Function
```python
def image_callback(self, msg: Image) -> None:
    # Process each incoming image
    height = msg.height
    width = msg.width
```

**How it works**:
- ROS 2 calls this function **automatically** when a message arrives
- The `msg` parameter contains the `Image` data
- **Non-blocking**: Callbacks should execute quickly (\<10ms ideal)

:::caution Callback Performance
Never do heavy processing in callbacks! For object detection or SLAM, use a **separate thread** or **timer** to process queued images.
:::

#### 3. Message Structure: sensor_msgs/Image
```python
msg.header.stamp       # Timestamp (when image was captured)
msg.height             # Image height in pixels
msg.width              # Image width in pixels
msg.encoding           # Pixel format ("rgb8", "bgr8", "mono8")
msg.data               # Raw pixel data (1D array)
```

## Running the Subscriber with a Simulated Camera

We don't have a physical camera yet, so let's use a **mock publisher** to test:

### Step 1: Create a Mock Camera Publisher

Save this as `mock_camera.py`:

```python
#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import numpy as np

class MockCamera(Node):
    def __init__(self):
        super().__init__('mock_camera')
        self.publisher = self.create_publisher(Image, '/camera/image_raw', 10)
        self.timer = self.create_timer(1.0 / 30.0, self.publish_frame)  # 30 FPS
        self.get_logger().info('Mock camera publishing at 30 FPS')

    def publish_frame(self):
        msg = Image()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.height = 480
        msg.width = 640
        msg.encoding = 'rgb8'
        msg.step = msg.width * 3  # 3 bytes per pixel (RGB)
        msg.data = np.random.randint(0, 255, (msg.height, msg.width, 3), dtype=np.uint8).tobytes()
        self.publisher.publish(msg)

def main():
    rclpy.init()
    node = MockCamera()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### Step 2: Run Both Nodes

**Terminal 1** (Publisher):
```bash
python3 mock_camera.py
```

**Terminal 2** (Subscriber):
```bash
python3 camera_subscriber.py
```

You should see:
```
[INFO] [camera_subscriber]: Received frame #30: 640x480 pixels, encoding=rgb8
[INFO] [camera_subscriber]: Received frame #60: 640x480 pixels, encoding=rgb8
```

### Step 3: Verify Communication

**Terminal 3** (Check topic info):
```bash
ros2 topic hz /camera/image_raw
```

Output:
```
average rate: 30.015
    min: 0.032s max: 0.034s std dev: 0.00045s window: 30
```

This confirms the camera is publishing at **30 Hz** (30 FPS).

## Services: A Quick Introduction

While topics handle streaming data, **services** handle one-time requests. Here's a simple example:

### Service Structure

A service has two parts:
1. **Request**: Data sent by the client
2. **Response**: Data returned by the server

Example: `AddTwoInts.srv`
```
# Request
int64 a
int64 b
---
# Response
int64 sum
```

### Calling a Service from Command Line

ROS 2 provides built-in services. Try this:

```bash
# List available services
ros2 service list

# Call the /add_two_ints service (if it exists)
ros2 service call /add_two_ints example_interfaces/srv/AddTwoInts "{a: 5, b: 3}"
```

Response:
```yaml
sum: 8
```

:::info Advanced Topic
Writing custom service servers and clients will be covered in advanced ROS 2 courses. For now, focus on understanding the **conceptual difference** between topics and services.
:::

## Topics vs Services: Decision Matrix

| Use Case | Communication Type | Reason |
|----------|-------------------|--------|
| Camera stream | **Topic** | Continuous data at 30 FPS |
| Lidar scans | **Topic** | Continuous data at 10 Hz |
| Battery voltage | **Topic** | Periodic updates |
| "Open gripper" | **Service** | One-time command with confirmation |
| "Get map size" | **Service** | Query current state |
| "Reset odometry" | **Service** | Configuration change |
| Long robot motion | **Action** | Use Actions (not covered yet) |

## Sim-to-Real: Deploying to Jetson Orin with RealSense

The same subscriber code works with a **real RealSense D435i camera**:

```bash
# On Jetson Orin (after installing RealSense ROS 2 driver)
ros2 launch realsense2_camera rs_launch.py

# In another terminal
python3 camera_subscriber.py
```

The subscriber doesn't care if images come from:
- A mock publisher (our test)
- Gazebo simulator
- **RealSense D435i** camera (real hardware)
- Recorded bag files (`ros2 bag play`)

This is the power of **abstraction**: write once, run anywhere!

:::tip Hardware Deployment
When deploying to Jetson Orin, the RealSense camera publishes to `/camera/color/image_raw`. Just change the topic name in your subscriber!
:::

## Common Mistakes

### Mistake 1: Not Storing the Subscription
```python
# ❌ Subscription gets garbage collected!
self.create_subscription(Image, '/camera', self.callback, 10)
# Missing: self.subscription = ...
```

**Fix**: Always store the subscription in `self.subscription`.

### Mistake 2: Blocking in Callbacks
```python
def image_callback(self, msg):
    time.sleep(5)  # ❌ Blocks other callbacks!
```

**Fix**: Callbacks should execute in \<10ms. Use timers for long processing.

### Mistake 3: Wrong Queue Size
```python
self.create_subscription(Image, '/camera', self.callback, 1)  # ❌ Too small!
```

**Fix**: For high-frequency topics (cameras), use queue size of 10+.

## Summary

In this chapter, you learned:

✅ **Topics** are for continuous streaming (camera, lidar, sensors)
✅ **Services** are for request-response (commands, queries)
✅ How to write a **subscriber node** that listens to `/camera/image_raw`
✅ The `image_callback()` pattern for processing messages
✅ How to test subscribers with **mock publishers**
✅ The same code works with **RealSense cameras on Jetson Orin**

## What's Next?

In **Chapter 4: The Body Schema (URDF)**, you'll learn how robots describe their physical structure to the computer. You'll write URDF (Unified Robot Description Format) XML to define a robot's links and joints—essential for simulation and motion planning.

## Further Reading

- [ROS 2 Topics Tutorial](https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Topics/Understanding-ROS2-Topics.html)
- [ROS 2 Services Tutorial](https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Services/Understanding-ROS2-Services.html)
- [sensor_msgs/Image Documentation](https://docs.ros2.org/latest/api/sensor_msgs/msg/Image.html)

---

**Next Chapter**: [Chapter 4: The Body Schema (URDF) →](./chapter-4-nervous-system.md)
