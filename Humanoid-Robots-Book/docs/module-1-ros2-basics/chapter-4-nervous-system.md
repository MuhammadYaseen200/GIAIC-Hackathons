---
sidebar_position: 4
title: Chapter 4 - The Body Schema
description: Defining robot physical structure with URDF
---

# Chapter 4: The Body Schema (URDF)

## Introduction

Imagine trying to control your arm without knowing where your elbow is, how long your forearm is, or which direction your wrist can bend. Impossible, right? Your brain has an internal **body schema**—a mental model of your physical structure.

Robots need the same thing! In this chapter, you'll learn how to describe a robot's physical structure using **URDF (Unified Robot Description Format)**—the XML-based language that tells ROS 2:
- What parts (links) make up the robot
- How those parts are connected (joints)
- The geometry, mass, and collision properties

By the end of this chapter, you'll be able to write URDF XML for robot components and understand how real robots like the **Unitree Go2** are described.

:::tip Learning Outcome
You'll write a simple URDF snippet for a generic robot leg and understand how links, joints, and coordinate frames work together.
:::

## Prerequisites

- **Hardware**: Standard laptop (Sim Mode, no physical robot required)
- **Software**:
  - Ubuntu 22.04 LTS with ROS 2 Humble
  - `urdf_tutorial` package: `sudo apt install ros-humble-urdf-tutorial`
  - Text editor with XML syntax highlighting
- **Prior Knowledge**:
  - Chapters 1-3 completed (nodes, topics, basic ROS 2)
  - Basic understanding of 3D coordinate systems (X, Y, Z axes)

:::note Hardware Requirements - Sim Mode
This chapter runs entirely in **simulation** on a standard laptop. No Jetson Orin, GPU, or physical robot (Unitree Go2) required. URDF visualization works on any Linux machine with ROS 2.
:::

## What is URDF?

**URDF (Unified Robot Description Format)** is an XML-based language for describing:
- **Mechanical structure**: Links and joints
- **Geometry**: Visual meshes (what you see) and collision shapes (what hits things)
- **Inertial properties**: Mass, center of gravity, inertia tensors
- **Sensors and actuators**: Cameras, lidars, motors

Think of URDF as the **blueprint** for your robot. Without it:
- Simulators (Gazebo, Isaac Sim) wouldn't know what your robot looks like
- Motion planners wouldn't know joint limits
- Visualization tools (RViz) couldn't display the robot

![Diagram: URDF Link-Joint Structure](../../static/img/module1/urdf-link-joint.png)

## The Building Blocks: Links and Joints

Every robot is built from two primitives:

### 1. Links (Rigid Bodies)

A **link** is a rigid part of the robot that doesn't deform:
- Robot base
- Upper arm
- Forearm
- Gripper finger
- Wheel

**Properties**:
- **Visual**: 3D mesh (`.stl`, `.dae` file) for rendering
- **Collision**: Simplified geometry (box, cylinder) for physics
- **Inertial**: Mass and inertia matrix for dynamics

### 2. Joints (Connections)

A **joint** connects two links and defines how they can move relative to each other:

| Joint Type | Description | Example |
|------------|-------------|---------|
| **Fixed** | No movement (welded) | Camera mounted on chassis |
| **Revolute** | Rotation around axis (limited range) | Robot elbow (0° to 180°) |
| **Continuous** | Unlimited rotation | Wheel spinning |
| **Prismatic** | Linear sliding | Elevator mechanism |

![Diagram: Joint Types Visualization](../../static/img/module1/joint-types.png)

## URDF Syntax: XML Structure

URDF files are XML documents with this structure:

```xml
<?xml version="1.0"?>
<robot name="my_robot">
  <!-- Links define rigid bodies -->
  <link name="base_link">
    <!-- Visual, collision, inertial properties -->
  </link>

  <link name="leg_link">
    <!-- Properties -->
  </link>

  <!-- Joints connect links -->
  <joint name="base_to_leg" type="revolute">
    <parent link="base_link"/>
    <child link="leg_link"/>
    <origin xyz="0 0 0" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
    <limit lower="0" upper="1.57" effort="10" velocity="1"/>
  </joint>
</robot>
```

### Key XML Tags

- `<robot>`: Root element (contains entire robot)
- `<link>`: Defines a rigid body
- `<joint>`: Connects two links
- `<origin>`: Position and orientation (xyz = position, rpy = roll-pitch-yaw)
- `<axis>`: Joint rotation/translation axis
- `<limit>`: Joint limits (angles, torque, speed)

## Writing Your First URDF: A Simple Robot Leg

Let's model a basic robot leg with two segments (thigh and shin) connected by a knee joint.

### Step 1: Create the URDF File

Save this as `simple_leg.urdf`:

```xml
<?xml version="1.0"?>
<robot name="simple_leg">

  <!-- BASE LINK (Hip) -->
  <link name="base_link">
    <visual>
      <geometry>
        <box size="0.1 0.1 0.1"/>  <!-- 10cm cube -->
      </geometry>
      <material name="blue">
        <color rgba="0 0 0.8 1"/>  <!-- Blue color -->
      </material>
    </visual>
    <collision>
      <geometry>
        <box size="0.1 0.1 0.1"/>
      </geometry>
    </collision>
    <inertial>
      <mass value="1.0"/>  <!-- 1 kg -->
      <inertia ixx="0.001" ixy="0" ixz="0" iyy="0.001" iyz="0" izz="0.001"/>
    </inertial>
  </link>

  <!-- THIGH LINK -->
  <link name="thigh_link">
    <visual>
      <geometry>
        <cylinder radius="0.05" length="0.3"/>  <!-- 5cm radius, 30cm long -->
      </geometry>
      <origin xyz="0 0 -0.15" rpy="0 0 0"/>  <!-- Center at midpoint -->
      <material name="red">
        <color rgba="0.8 0 0 1"/>
      </material>
    </visual>
    <collision>
      <geometry>
        <cylinder radius="0.05" length="0.3"/>
      </geometry>
      <origin xyz="0 0 -0.15" rpy="0 0 0"/>
    </collision>
    <inertial>
      <mass value="2.0"/>  <!-- 2 kg -->
      <origin xyz="0 0 -0.15" rpy="0 0 0"/>
      <inertia ixx="0.015" ixy="0" ixz="0" iyy="0.015" iyz="0" izz="0.0005"/>
    </inertial>
  </link>

  <!-- HIP JOINT (connects base to thigh) -->
  <joint name="hip_joint" type="revolute">
    <parent link="base_link"/>
    <child link="thigh_link"/>
    <origin xyz="0 0 0" rpy="0 0 0"/>
    <axis xyz="0 1 0"/>  <!-- Rotate around Y-axis (forward-backward swing) -->
    <limit lower="-1.57" upper="1.57" effort="50" velocity="2"/>
    <!-- Limits: -90° to +90°, max torque 50 Nm, max speed 2 rad/s -->
  </joint>

  <!-- SHIN LINK -->
  <link name="shin_link">
    <visual>
      <geometry>
        <cylinder radius="0.04" length="0.3"/>  <!-- Slightly thinner -->
      </geometry>
      <origin xyz="0 0 -0.15" rpy="0 0 0"/>
      <material name="green">
        <color rgba="0 0.8 0 1"/>
      </material>
    </visual>
    <collision>
      <geometry>
        <cylinder radius="0.04" length="0.3"/>
      </geometry>
      <origin xyz="0 0 -0.15" rpy="0 0 0"/>
    </collision>
    <inertial>
      <mass value="1.5"/>  <!-- 1.5 kg -->
      <origin xyz="0 0 -0.15" rpy="0 0 0"/>
      <inertia ixx="0.011" ixy="0" ixz="0" iyy="0.011" iyz="0" izz="0.0003"/>
    </inertial>
  </link>

  <!-- KNEE JOINT (connects thigh to shin) -->
  <joint name="knee_joint" type="revolute">
    <parent link="thigh_link"/>
    <child link="shin_link"/>
    <origin xyz="0 0 -0.3" rpy="0 0 0"/>  <!-- At bottom of thigh -->
    <axis xyz="0 1 0"/>  <!-- Rotate around Y-axis -->
    <limit lower="0" upper="2.35" effort="30" velocity="2"/>
    <!-- Limits: 0° to 135° (knee can only bend one way) -->
  </joint>

</robot>
```

### URDF Breakdown

#### Link Definition
```xml
<link name="thigh_link">
  <visual>...</visual>      <!-- What you see in RViz/Gazebo -->
  <collision>...</collision> <!-- For physics collision detection -->
  <inertial>...</inertial>   <!-- For dynamics simulation -->
</link>
```

#### Joint Definition
```xml
<joint name="hip_joint" type="revolute">
  <parent link="base_link"/>  <!-- Fixed link -->
  <child link="thigh_link"/>  <!-- Moving link -->
  <origin xyz="0 0 0"/>       <!-- Position of joint -->
  <axis xyz="0 1 0"/>         <!-- Rotation axis (Y) -->
  <limit lower="-1.57" upper="1.57"/>  <!-- ±90° in radians -->
</joint>
```

:::info Coordinate System
ROS 2 uses the **right-hand rule**:
- **X**: Forward (red)
- **Y**: Left (green)
- **Z**: Up (blue)
- Angles in **radians** (π ≈ 3.14 rad = 180°)
:::

## Visualizing URDF in RViz

Let's see the robot leg in 3D!

### Step 1: Check URDF Validity
```bash
check_urdf simple_leg.urdf
```

Output:
```
robot name is: simple_leg
---------- Successfully Parsed XML ---------------
root Link: base_link has 1 child(ren)
    child(1):  thigh_link
        child(1):  shin_link
```

### Step 2: Launch RViz Visualization
```bash
ros2 launch urdf_tutorial display.launch.py model:=simple_leg.urdf
```

You'll see:
- A 3D model of your leg
- **Joint State Publisher GUI** (sliders to move joints)
- **TF frames** (coordinate axes for each link)

:::tip Interactive Visualization
Drag the sliders in the "Joint State Publisher" window to bend the hip and knee joints. Watch the leg move in real time!
:::

![Diagram: RViz URDF Visualization](../../static/img/module1/rviz-urdf-display.png)

## Real-World Example: Unitree Go2 Quadruped

The **Unitree Go2** is a commercial quadruped robot (4-legged, like a robotic dog). Its URDF defines:
- **1 base link** (body chassis)
- **4 legs** × **3 links each** (hip, thigh, shin) = 12 leg links
- **12 revolute joints** (3 per leg: hip abduction, hip flexion, knee)
- **Sensors**: IMU, cameras, lidar

### Simplified Unitree Go2 Leg Structure
```
base_link
  └─ hip_abduction_joint (side-to-side)
      └─ hip_link
          └─ hip_flexion_joint (forward-backward)
              └─ thigh_link
                  └─ knee_joint
                      └─ shin_link
```

:::note Unitree Go2 URDF Availability
The official Unitree Go2 URDF is available in the [unitree_ros2 repository](https://github.com/unitreerobotics/unitree_ros2). You'll use this in Module 2 (Digital Twin) to simulate the robot in Gazebo.
:::

## From URDF to Simulation (Preview)

URDF is the foundation for:

1. **Gazebo Simulation** (Module 2):
   - Physics engine uses collision geometry
   - Visual rendering uses meshes
   - Joint controllers apply torque

2. **Motion Planning** (Advanced):
   - MoveIt uses joint limits and kinematics
   - Collision avoidance uses collision shapes

3. **State Estimation**:
   - TF (Transform) tree broadcasts link positions
   - Robot State Publisher converts joint angles → 3D poses

## Common URDF Mistakes

### Mistake 1: Missing Parent-Child Relationship
```xml
<!-- ❌ Joint has no parent! -->
<joint name="broken_joint" type="revolute">
  <child link="leg"/>
  <!-- Missing <parent> tag -->
</joint>
```

**Fix**: Every joint must have exactly one parent and one child.

### Mistake 2: Degrees Instead of Radians
```xml
<!-- ❌ 90 radians = 5156 degrees! -->
<limit lower="0" upper="90"/>
```

**Fix**: Use radians (90° = 1.57 rad).

### Mistake 3: Wrong Axis Direction
```xml
<!-- ❌ Knee bends sideways! -->
<axis xyz="1 0 0"/>  <!-- Should be Y-axis -->
```

**Fix**: Visualize in RViz and test joint motion.

## Sim-to-Real: Deploying URDF to Physical Robots

The same URDF works for:
- **Gazebo Simulation** (on your laptop)
- **Isaac Sim** (NVIDIA's GPU-accelerated simulator)
- **Physical Unitree Go2** (real robot hardware)

When deploying to hardware:
1. URDF joint names must match **motor controller IDs**
2. Joint limits must match **physical hard stops** (to prevent damage)
3. Inertial properties affect **balance algorithms**

:::caution Hardware Safety
**Always** set conservative joint limits in URDF! If you specify a knee can bend 360°, but the physical robot has a hard stop at 135°, you'll **break the motor**!
:::

## Summary

In this chapter, you learned:

✅ **URDF** is the XML language for describing robot structure
✅ **Links** are rigid bodies (thigh, shin, base)
✅ **Joints** connect links (revolute, continuous, fixed, prismatic)
✅ How to write **URDF XML** for a simple robot leg
✅ How to **visualize URDF** in RViz with `check_urdf` and `display.launch.py`
✅ Real robots like **Unitree Go2** use URDF for simulation and control
✅ The same URDF works in **sim (Gazebo) and real (Jetson Orin on Go2)**

## What's Next?

Congratulations! You've completed **Module 1: ROS 2 Basics & Nervous System**. You now understand:
- Nodes and computation graphs
- Writing Python nodes (publishers and subscribers)
- Topics vs. services
- Describing robot structure with URDF

**In Module 2: Digital Twin Development**, you'll:
- Create a full digital twin in Gazebo
- Simulate the Unitree Go2 robot
- Learn URDF advanced features (meshes, sensors, plugins)
- Test robot behaviors in physics simulation

## Further Reading

- [URDF XML Specification](http://wiki.ros.org/urdf/XML)
- [URDF Tutorials (ROS 2)](https://docs.ros.org/en/humble/Tutorials/Intermediate/URDF/URDF-Main.html)
- [Unitree Go2 Robot](https://www.unitree.com/go2)
- [Gazebo Simulation (Preview)](https://gazebosim.org/)

---

**Module 1 Complete!** 🎉

**Next Module**: [Module 2: Digital Twin Development →](../module-2-digital-twin/chapter-5-digital-twin-intro.md)
