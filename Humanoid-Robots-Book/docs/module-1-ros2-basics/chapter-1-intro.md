---
sidebar_position: 1
title: Chapter 1 - The Nervous System
description: Understanding ROS 2 Nodes as the neurons of a robot
---

# Chapter 1: The Nervous System (Nodes & Graphs)

## Introduction

Welcome to the world of **Physical AI**! In this chapter, we'll explore how robots think and communicate by drawing parallels to the human nervous system. Just as your brain uses neurons to send signals throughout your body, robots use **ROS 2 Nodes** to coordinate sensors, actuators, and decision-making processes.

By the end of this chapter, you'll understand:
- What ROS 2 Nodes are and why they're fundamental
- How the ROS 2 computation graph works
- The biological analogy: Nodes as neurons
- How to visualize and debug node communication

:::tip Learning Outcome
You'll be able to explain how a robot's "nervous system" is organized and identify the role of individual nodes in a robotic system.
:::

## Prerequisites

Before diving in, ensure you have:
- **Hardware**: Standard laptop (no GPU required for simulation)
- **Software**: Ubuntu 22.04 LTS (or Docker with ROS 2 Humble)
- **Basic Knowledge**: Familiarity with command-line interfaces
- **ROS 2 Installation**: ROS 2 Humble installed ([Installation Guide](https://docs.ros.org/en/humble/Installation.html))

:::note Hardware Requirements - Sim Mode
This chapter runs entirely in **simulation mode** on a standard laptop. No specialized hardware (Jetson Orin, GPU, or physical robot) is required. All examples work on:
- Intel/AMD CPU (2+ cores recommended)
- 4GB RAM minimum
- Ubuntu 22.04 or compatible Linux distribution
:::

## The Biological Analogy: Your Brain as a Robot

Let's start with a familiar concept: your own nervous system.

When you touch a hot stove, here's what happens:
1. **Sensory neurons** (in your fingertips) detect heat
2. Signals travel to your **spinal cord** (reflex center)
3. **Motor neurons** instantly tell your arm muscles to pull away
4. Your **brain** (central processing) receives the signal slightly later and says "Ouch!"

This distributed system has key properties:
- **Parallel processing**: Multiple neurons work simultaneously
- **Specialized roles**: Some neurons sense, others move, others think
- **Communication pathways**: Neurons talk via electrical signals

Robots work the same way! Instead of neurons, we have **Nodes**. Instead of nerve pathways, we have **Topics** and **Services**. Let's see how.

![Diagram: Human Nervous System vs. ROS 2 Node Graph](../../static/img/module1/nervous-system-analogy.png)

## What is a ROS 2 Node?

A **Node** is a single-purpose program that performs one specific task in a robotic system.

**Examples of Nodes**:
- **Camera Driver Node**: Reads images from a physical camera sensor
- **Object Detection Node**: Analyzes images to find objects (e.g., "bottle detected at 2 meters")
- **Motion Planning Node**: Decides how the robot should move its arm to grab the bottle
- **Motor Controller Node**: Sends voltage signals to physical motors

:::info Key Principle: Single Responsibility
Each node should do **one thing well**. Don't create a mega-node that does everything! This is like having specialized brain regions (visual cortex for seeing, motor cortex for moving).
:::

### Why Split Into Nodes?

Imagine building a self-driving car. You could write one giant program that:
- Reads camera feeds
- Detects lanes and traffic lights
- Plans routes
- Controls steering and brakes

But if the camera code crashes, the entire car shuts down!

Instead, ROS 2 uses **modular nodes**:
```
[Camera Node] → [Lane Detection Node] → [Path Planning Node] → [Steering Control Node]
```

If the camera node fails, the other nodes can detect the failure and take safe action (e.g., pull over).

## The ROS 2 Computation Graph

When multiple nodes run together, they form a **computation graph**. This graph shows:
- **Nodes** (circles): Individual programs
- **Topics** (arrows): Data streams between nodes (e.g., camera images)
- **Services** (dashed lines): Request-response calls (e.g., "Open gripper now!")

![Diagram: ROS 2 Computation Graph for a Mobile Robot](../../static/img/module1/ros2-graph-example.png)

### Example: Autonomous Delivery Robot

Let's design a simple delivery robot's nervous system:

```
┌─────────────────┐         ┌──────────────────┐
│  Lidar Sensor   │────────▶│  Map Builder     │
│  Node           │  /scan  │  Node            │
└─────────────────┘         └──────────────────┘
                                     │ /map
                                     ▼
┌─────────────────┐         ┌──────────────────┐
│  GPS Sensor     │────────▶│  Path Planner    │
│  Node           │ /gps    │  Node            │
└─────────────────┘         └──────────────────┘
                                     │ /cmd_vel
                                     ▼
                            ┌──────────────────┐
                            │  Wheel Motors    │
                            │  Node            │
                            └──────────────────┘
```

**How it works**:
1. **Lidar Sensor Node** publishes obstacle data on `/scan` topic
2. **GPS Sensor Node** publishes location on `/gps` topic
3. **Map Builder Node** subscribes to `/scan` and creates a map
4. **Path Planner Node** subscribes to `/map` and `/gps`, calculates safe routes
5. **Wheel Motors Node** subscribes to `/cmd_vel` (velocity commands) and moves the robot

Notice how each node has a **clear job** and communicates through **named topics**.

## Nodes vs. Nodelets vs. Components

:::caution Advanced Concept
This section is for context. Beginners can skip to the next section!
:::

ROS 2 has evolved from ROS 1 in how nodes are managed:

| Concept | Description | Use Case |
|---------|-------------|----------|
| **Node** | Separate operating system process | Default choice (isolated, safe) |
| **Component** | Shared library loaded into a container | High-performance vision pipelines (reduces memory copies) |

For this course, we'll use **standard nodes** (separate processes). Components are an optimization for advanced use cases like real-time camera processing on Jetson Orin.

## Visualizing the Graph with `rqt_graph`

ROS 2 provides a tool to visualize the live computation graph.

**Launch the graph viewer**:
```bash
# Terminal 1: Start a demo (turtlesim)
ros2 run turtlesim turtlesim_node

# Terminal 2: Start keyboard control
ros2 run turtlesim turtle_teleop_key

# Terminal 3: Visualize the graph
rqt_graph
```

You'll see:
- Two nodes: `/turtlesim` and `/teleop_turtle`
- One topic: `/turtle1/cmd_vel` (velocity commands from keyboard to simulator)

:::tip Interactive Exercise
Try running `rqt_graph` while experimenting with different ROS 2 demos. Notice how the graph changes as you start/stop nodes!
:::

## Nodes Are Not Magic: They're Just Programs

Here's the secret: **a ROS 2 node is just a regular program** (Python or C++) that:
1. Imports the ROS 2 library (`rclpy` for Python, `rclcpp` for C++)
2. Registers itself with the ROS 2 system ("Hi, I'm the camera_driver node!")
3. Creates publishers, subscribers, or services
4. Runs a loop to process data

In Chapter 2, you'll write your first node in Python. For now, understand the **mental model**: nodes are independent programs talking over a shared network.

## The Discovery Mechanism: How Nodes Find Each Other

When you start a node, it doesn't need a "master server" (unlike ROS 1). ROS 2 uses **DDS (Data Distribution Service)** for automatic discovery.

**How it works**:
1. Node A starts and broadcasts: "I publish images on `/camera/rgb`"
2. Node B starts and broadcasts: "I subscribe to `/camera/rgb`"
3. DDS automatically connects them (like Bluetooth pairing!)

:::note No Central Master
ROS 2 is **fully distributed**. If one node crashes, others continue running. This is critical for robotic safety!
:::

## Sim-to-Real: From Laptop to Jetson Orin

Right now, you're running nodes in **simulation** on your laptop. Later in this course, you'll deploy the same code to **physical hardware**:

- **Jetson Orin Nano**: For vision processing (object detection, SLAM)
- **Unitree Go2 Robot**: Quadruped robot with onboard compute
- **RealSense Camera**: Depth sensor for 3D perception

The beauty of ROS 2: **the same node code works in simulation and reality**. You develop on your laptop, then deploy to the robot with minimal changes.

:::tip Sim-to-Real Strategy
Always test your nodes in simulation first (Gazebo, Isaac Sim). Fix bugs on your laptop before risking hardware damage!
:::

## Summary

In this chapter, you learned:

✅ **Nodes are the neurons** of a robot's nervous system
✅ Each node has a **single, well-defined purpose**
✅ Nodes communicate via **topics** (data streams) and **services** (request-response)
✅ The **computation graph** shows how nodes connect
✅ ROS 2 uses **DDS for automatic discovery** (no central master)
✅ The same node code runs on **laptops (sim) and robots (real)**

## What's Next?

In **Chapter 2: Speaking Python (rclpy)**, you'll write your first ROS 2 node from scratch. You'll create a simple publisher that says "Hello, Physical AI!" and learn the anatomy of a production-ready node.

## Further Reading

- [ROS 2 Concepts: Nodes](https://docs.ros.org/en/humble/Concepts/Basic/About-Nodes.html)
- [ROS 2 DDS and Discovery](https://docs.ros.org/en/humble/Concepts/Intermediate/About-Domain-ID.html)
- [Computation Graph Visualization](https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Nodes/Understanding-ROS2-Nodes.html)

---

**Next Chapter**: [Chapter 2: Speaking Python (rclpy) →](./chapter-2-pub-sub.md)
