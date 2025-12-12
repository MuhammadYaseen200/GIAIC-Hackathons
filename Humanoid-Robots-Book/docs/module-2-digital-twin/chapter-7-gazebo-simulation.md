---
sidebar_position: 3
title: Chapter 7 - Gazebo Simulation
description: Running and controlling robots in Gazebo physics simulation
---

# Chapter 7: Gazebo Simulation

## Introduction

You've built a digital twin (Chapter 5) and created production-grade URDF files (Chapter 6). Now it's time to **bring your robot to life** in Gazebo—the open-source physics simulator used by NASA, Toyota, and thousands of robotics companies worldwide.

In this chapter, you'll:
- Launch the Unitree Go2 in Gazebo
- Control joints via ROS 2 topics
- Read simulated sensor data (camera, lidar, IMU)
- Test physics scenarios (gravity, friction, collisions)

By the end, you'll have a fully functional digital twin you can program just like a real robot.

:::tip Learning Outcome
You'll run Gazebo simulations, publish joint commands, subscribe to sensor data, and verify robot behavior before deploying to physical hardware.
:::

## Prerequisites

- **Hardware**: Standard laptop with 8GB+ RAM (Gazebo runs on CPU)
- **Software**:
  - Ubuntu 22.04 LTS with ROS 2 Humble
  - Gazebo Harmonic: `sudo apt install ros-humble-gazebo-ros-pkgs`
  - `ros2_control`: `sudo apt install ros-humble-ros2-control ros-humble-ros2-controllers`
- **Prior Knowledge**:
  - Chapters 5-6 (Digital Twins, Advanced URDF)
  - Module 1 (ROS 2 nodes, topics)

:::note Hardware Requirements - Sim Mode
Gazebo runs efficiently on **standard laptop CPUs** (Intel i5/AMD Ryzen 5+). No NVIDIA GPU required for basic physics. For advanced rendering (ray tracing, shadows), a GPU helps but is optional.
:::

## What is Gazebo?

**Gazebo** is a 3D robot simulator with:
- **Physics engines**: ODE, Bullet, Simbody, DART (choose based on use case)
- **Sensor simulation**: Camera, lidar, depth, IMU, GPS
- **ROS 2 integration**: Bidirectional topic communication
- **Plugins**: Custom behaviors (controllers, sensors, world objects)

Think of Gazebo as a **physics-accurate video game** where your robot obeys real-world laws (gravity, friction, inertia).

![Diagram: Gazebo Architecture](../../static/img/module2/gazebo-architecture.png)

### Gazebo vs. Other Simulators

| Simulator | Best For | Hardware | Cost |
|-----------|----------|----------|------|
| **Gazebo** | General robotics (manipulation, mobile) | CPU (8GB RAM) | Free |
| **Isaac Sim** | GPU-accelerated vision, RL training | RTX 4070 Ti+ | Free (NVIDIA) |
| **Webots** | Education, multi-robot | CPU (4GB RAM) | Free |
| **MuJoCo** | Fast physics, RL (DeepMind) | CPU | Free |
| **V-REP (CoppeliaSim)** | Academic research | CPU/GPU | Free |

**Why Gazebo for this course**: Best ROS 2 integration + most widely used in industry.

## Installing Gazebo Harmonic

If not already installed:

```bash
# Install Gazebo Harmonic
sudo apt update
sudo apt install ros-humble-gazebo-ros-pkgs

# Install ros2_control for joint control
sudo apt install ros-humble-ros2-control ros-humble-ros2-controllers

# Verify installation
gazebo --version
# Output: Gazebo multi-robot simulator, version 11.x.x
```

## Launching Your First Simulation

### Step 1: Test Gazebo with a Built-In World

```bash
# Launch empty world
gazebo
```

You should see the Gazebo GUI with:
- **Scene View**: 3D visualization
- **World** tab: List of objects
- **Time** panel: Simulation time controls (play, pause, step)

Press **Ctrl+C** to close.

### Step 2: Spawn a Simple Robot

Let's use a ROS 2 launch file to spawn a robot:

```bash
# Launch TurtleBot3 (simple example robot)
ros2 launch turtlebot3_gazebo empty_world.launch.py
```

You'll see:
- Gazebo window with a small robot
- ROS 2 topics active (`/cmd_vel`, `/odom`, `/scan`)

**Control the robot**:
```bash
# In a new terminal
ros2 run turtlebot3_teleop teleop_keyboard
```

Use arrow keys to drive! This demonstrates the **sim-to-real principle**: the same `/cmd_vel` topic works in simulation and on physical TurtleBot3 hardware.

## Understanding Gazebo Launch Files

Launch files automate:
1. Starting Gazebo
2. Loading a world file (`.world`)
3. Spawning robots (from URDF)
4. Starting ROS 2 controllers

### Example: Launch File for Unitree Go2

Create `go2_gazebo.launch.py`:

```python
#!/usr/bin/env python3
"""
Gazebo launch file for Unitree Go2 digital twin.
Spawns the Go2 robot in an empty world with physics.
"""

import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    """
    Generate launch description for Gazebo simulation.

    Returns:
        LaunchDescription with Gazebo and robot spawner nodes
    """
    # Package directories
    gazebo_ros_pkg = get_package_share_directory('gazebo_ros')
    go2_description_pkg = get_package_share_directory('unitree_go2_description')

    # Paths
    urdf_file = os.path.join(go2_description_pkg, 'urdf', 'go2.urdf')
    world_file = os.path.join(go2_description_pkg, 'worlds', 'empty.world')

    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    # Gazebo server (physics)
    gazebo_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros_pkg, 'launch', 'gzserver.launch.py')
        ),
        launch_arguments={'world': world_file}.items()
    )

    # Gazebo client (GUI)
    gazebo_client = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros_pkg, 'launch', 'gzclient.launch.py')
        )
    )

    # Read URDF file
    with open(urdf_file, 'r') as file:
        robot_description = file.read()

    # Robot state publisher (broadcasts TF frames)
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': robot_description
        }]
    )

    # Spawn robot in Gazebo
    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name='spawn_go2',
        output='screen',
        arguments=[
            '-entity', 'go2',
            '-topic', '/robot_description',
            '-x', '0', '-y', '0', '-z', '0.5'  # Spawn 50cm above ground
        ]
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        gazebo_server,
        gazebo_client,
        robot_state_publisher,
        spawn_robot
    ])
```

**Launch it**:
```bash
ros2 launch unitree_go2_description go2_gazebo.launch.py
```

## Controlling Joints in Gazebo

### Method 1: Manual Control (GUI)

Gazebo GUI → **Insert** tab → Right-click robot → **Apply Force/Torque**

Use this for testing individual joints.

### Method 2: ROS 2 Topics (Programmatic Control)

Gazebo subscribes to `/joint_trajectory_controller/joint_trajectory`:

**Step 2a: Applying @ROS2-Architect skill** (OOP joint controller)

```python
#!/usr/bin/env python3
"""
Joint Controller for Unitree Go2 in Gazebo
Sends joint position commands to move robot legs.

Author: Physical AI Course
License: MIT
"""

import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
from typing import List, Dict
import math


class Go2JointController(Node):
    """
    ROS 2 node for controlling Unitree Go2 joint positions.

    This demonstrates:
    - Publishing to joint_trajectory topic
    - Coordinating multiple joints (12 total for 4 legs)
    - Time-based trajectory execution
    """

    def __init__(self) -> None:
        """Initialize the Go2 joint controller node."""
        super().__init__('go2_joint_controller')

        # Publisher for joint trajectories
        self.publisher_ = self.create_publisher(
            JointTrajectory,
            '/joint_trajectory_controller/joint_trajectory',
            10
        )

        # Joint names for Unitree Go2 (4 legs × 3 joints each)
        self.joint_names: List[str] = [
            # Front Left leg
            'FL_hip_abduction_joint', 'FL_hip_flexion_joint', 'FL_knee_joint',
            # Front Right leg
            'FR_hip_abduction_joint', 'FR_hip_flexion_joint', 'FR_knee_joint',
            # Rear Left leg
            'RL_hip_abduction_joint', 'RL_hip_flexion_joint', 'RL_knee_joint',
            # Rear Right leg
            'RR_hip_abduction_joint', 'RR_hip_flexion_joint', 'RR_knee_joint'
        ]

        # Timer to execute motion commands
        self.timer = self.create_timer(2.0, self.send_command)

        self.get_logger().info('Go2 Joint Controller started. Sending commands every 2 seconds.')

    def send_command(self) -> None:
        """
        Send a joint trajectory command to Gazebo.

        Example: Move all legs to a "standing" pose.
        """
        msg = JointTrajectory()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.joint_names = self.joint_names

        # Define target joint positions (in radians)
        # Standing pose: legs straight down
        point = JointTrajectoryPoint()
        point.positions = [
            # FL leg: abduction=0, hip=0, knee=-1.5 (bent)
            0.0, 0.0, -1.5,
            # FR leg
            0.0, 0.0, -1.5,
            # RL leg
            0.0, 0.0, -1.5,
            # RR leg
            0.0, 0.0, -1.5
        ]

        # Velocities (optional, set to zero for position control)
        point.velocities = [0.0] * 12

        # Time to reach this position (2 seconds)
        point.time_from_start = Duration(sec=2, nanosec=0)

        msg.points = [point]

        self.publisher_.publish(msg)
        self.get_logger().info('Sent standing pose command to robot.')


def main(args=None) -> None:
    """
    Entry point for the joint controller node.

    Args:
        args: Command-line arguments (optional)
    """
    rclpy.init(args=args)

    node: Go2JointController | None = None

    try:
        node = Go2JointController()
        rclpy.spin(node)

    except KeyboardInterrupt:
        if node:
            node.get_logger().info('Shutting down joint controller...')

    except Exception as e:
        if node:
            node.get_logger().error(f'Unexpected error: {e}')
        raise

    finally:
        if node:
            node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
```

**Run it**:
```bash
python3 go2_joint_controller.py
```

The robot's legs will move to a standing pose!

## Reading Sensor Data

### Subscribing to Simulated Camera

The camera we added in Chapter 6 publishes to `/go2/camera/image_raw`. Let's subscribe:

**Step 2b: Applying @ROS2-Architect skill** (OOP camera subscriber)

```python
#!/usr/bin/env python3
"""
Camera Subscriber for Gazebo Simulation
Receives images from simulated camera and logs metadata.

Author: Physical AI Course
License: MIT
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from typing import Optional


class GazeboCameraSubscriber(Node):
    """
    Subscribes to simulated camera topic in Gazebo.

    Demonstrates:
    - Receiving images from Gazebo plugins
    - Processing sensor data in simulation
    """

    def __init__(self) -> None:
        """Initialize the camera subscriber node."""
        super().__init__('gazebo_camera_subscriber')

        # Subscribe to Gazebo camera topic
        self.subscription = self.create_subscription(
            Image,
            '/go2/camera/image_raw',
            self.image_callback,
            10
        )

        self.frame_count: int = 0

        self.get_logger().info('Gazebo Camera Subscriber started.')

    def image_callback(self, msg: Image) -> None:
        """
        Callback for processing camera images.

        Args:
            msg: Image message from Gazebo camera plugin
        """
        self.frame_count += 1

        # Log every 30th frame (once per second at 30 FPS)
        if self.frame_count % 30 == 0:
            self.get_logger().info(
                f'Received frame #{self.frame_count}: '
                f'{msg.width}x{msg.height}, encoding={msg.encoding}'
            )


def main(args: Optional[list] = None) -> None:
    """Entry point for camera subscriber node."""
    rclpy.init(args=args)

    node: Optional[GazeboCameraSubscriber] = None

    try:
        node = GazeboCameraSubscriber()
        rclpy.spin(node)

    except KeyboardInterrupt:
        if node:
            node.get_logger().info('Shutting down...')

    finally:
        if node:
            node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
```

## Testing Physics: Dropping the Robot

Let's verify gravity and collision physics work correctly:

```bash
# Spawn robot 2 meters above ground
ros2 run gazebo_ros spawn_entity.py -entity go2 -topic /robot_description -z 2.0
```

**What should happen**:
1. Robot falls due to gravity (9.81 m/s²)
2. Legs collide with ground
3. Robot bounces slightly (if damping < 1.0)
4. Robot settles into stable pose

**If robot falls through floor**: Check collision meshes in URDF!

:::caution Physics Debugging
If your robot behaves unrealistically (floating, exploding, vibrating), check:
1. **Inertial properties**: Wrong mass/inertia
2. **Collision geometry**: Overlapping meshes
3. **Joint limits**: Unrealistic ranges
4. **Physics engine**: Try switching ODE → Bullet
:::

## Advanced: Walking Gait Simulation

To make the Go2 walk, you need a **gait controller** (pattern of leg movements):

```python
# Simplified trotting gait (diagonal legs move together)
def trot_gait(t: float) -> Dict[str, float]:
    """
    Generate joint positions for trotting gait.

    Args:
        t: Time in seconds

    Returns:
        Dictionary of joint_name → position (radians)
    """
    frequency = 1.0  # Hz (1 step per second)
    phase = 2 * math.pi * frequency * t

    return {
        # Front Left & Rear Right (synchronized)
        'FL_hip_flexion_joint': 0.5 * math.sin(phase),
        'RR_hip_flexion_joint': 0.5 * math.sin(phase),

        # Front Right & Rear Left (opposite phase)
        'FR_hip_flexion_joint': 0.5 * math.sin(phase + math.pi),
        'RL_hip_flexion_joint': 0.5 * math.sin(phase + math.pi),

        # Knees (synchronized with hips)
        'FL_knee_joint': -1.5 + 0.3 * math.sin(phase),
        'RR_knee_joint': -1.5 + 0.3 * math.sin(phase),
        'FR_knee_joint': -1.5 + 0.3 * math.sin(phase + math.pi),
        'RL_knee_joint': -1.5 + 0.3 * math.sin(phase + math.pi),
    }
```

**Note**: Real walking controllers (like Unitree's proprietary firmware) use **Model Predictive Control (MPC)** or **Reinforcement Learning (RL)**, covered in Module 3 (Isaac Gym).

## Gazebo Worlds: Custom Environments

Create custom test environments in `.world` files:

```xml
<?xml version="1.0"?>
<sdf version="1.6">
  <world name="staircase_world">
    <include>
      <uri>model://sun</uri>
    </include>
    <include>
      <uri>model://ground_plane</uri>
    </include>

    <!-- Add stairs -->
    <model name="stairs">
      <static>true</static>
      <link name="step1">
        <pose>1 0 0.1 0 0 0</pose>
        <collision name="collision">
          <geometry>
            <box><size>0.3 1 0.2</size></box>
          </geometry>
        </collision>
        <visual name="visual">
          <geometry>
            <box><size>0.3 1 0.2</size></box>
          </geometry>
        </visual>
      </link>
      <!-- Add more steps... -->
    </model>
  </world>
</sdf>
```

Load it:
```bash
gazebo staircase_world.world
```

## Sim-to-Real: Deploying to Jetson Orin

The code you write for Gazebo **works identically** on the real Unitree Go2:

| Component | Gazebo | Real Go2 on Jetson Orin |
|-----------|--------|-------------------------|
| Joint Controller | Publishes to `/joint_trajectory_controller/joint_trajectory` | Same topic! |
| Camera Subscriber | Subscribes to `/go2/camera/image_raw` | RealSense publishes to same topic |
| Launch File | Starts Gazebo simulation | Starts hardware drivers |

**Key difference**: On hardware, use Unitree's motor controllers instead of Gazebo plugins.

:::tip Deployment Strategy
1. Develop algorithm in Gazebo (safe, fast iteration)
2. Test 1000+ scenarios (stairs, slopes, obstacles)
3. Deploy to real Go2 (minimal tuning, <5% changes)
:::

## Summary

In this chapter, you learned:

✅ How to launch **Gazebo** and spawn robots from URDF
✅ Creating **ROS 2 launch files** for automated setup
✅ Controlling joints via `/joint_trajectory_controller`
✅ Reading **simulated sensor data** (camera, lidar, IMU)
✅ Testing **physics** (gravity, collisions, dynamics)
✅ Building **custom Gazebo worlds** (stairs, obstacles)
✅ The **sim-to-real pipeline**: same code for simulation and hardware

## What's Next?

**Congratulations!** You've completed **Module 2: Digital Twin Development**. You now know:
- What digital twins are (Chapter 5)
- How to create production URDFs (Chapter 6)
- How to simulate robots in Gazebo (Chapter 7)

**In Module 3: Isaac Gym & Sim**, you'll:
- Use GPU-accelerated simulation (NVIDIA Isaac Sim)
- Train robots with Reinforcement Learning (RL)
- Perform massively parallel sim-to-real experiments (10,000+ robots)

:::note GPU Requirement
Module 3 requires an **NVIDIA GPU** (RTX 4070 Ti recommended, RTX 3060 minimum). If you don't have a GPU, you can use cloud services (AWS, Google Colab Pro+) or skip to Module 4 (VLA models).
:::

## Further Reading

- [Gazebo Documentation](https://gazebosim.org/docs)
- [ros2_control Tutorials](https://control.ros.org/master/doc/ros2_control/controller_manager/doc/userdoc.html)
- [Unitree Go2 Simulation](https://github.com/unitreerobotics/unitree_ros2)
- [Gazebo Plugins Reference](https://classic.gazebosim.org/tutorials?cat=connect_ros)

---

**Module 2 Complete!** 🎉

**Next Module**: [Module 3: Isaac Gym & Sim →](../module-3-isaac/chapter-8-isaac-gym-intro.md)
