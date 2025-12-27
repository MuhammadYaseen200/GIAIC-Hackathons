---
sidebar_position: 2
title: Chapter 6 - URDF Modeling (Advanced)
description: Creating production-grade robot descriptions with meshes and sensors
---

# Chapter 6: URDF Modeling (Advanced)

## Introduction

In Module 1 (Chapter 4), you learned URDF basics: links, joints, and simple geometry. But production robots like the **Unitree Go2** don't use primitive shapes (boxes, cylinders)—they use **high-fidelity 3D meshes**, realistic **inertial properties**, and **sensor plugins**.

In this chapter, you'll level up from basic URDF to **production-grade robot descriptions** that work in Gazebo simulation. You'll learn how to:
- Import 3D meshes (`.stl`, `.dae`) from CAD software
- Calculate inertial properties accurately
- Add simulated sensors (cameras, lidar, IMU)
- Use Gazebo plugins for ROS 2 integration

By the end, you'll have a complete URDF for a simplified Unitree Go2 digital twin.

:::tip Learning Outcome
You'll create a production-ready URDF with 3D meshes, realistic physics, and Gazebo plugins for sensors and control.
:::

## Prerequisites

- **Hardware**: Standard laptop (Gazebo runs on CPU, no GPU required)
- **Software**:
  - Ubuntu 22.04 LTS with ROS 2 Humble
  - Gazebo Harmonic: `sudo apt install ros-humble-gazebo-ros-pkgs`
  - `xacro` tool: `sudo apt install ros-humble-xacro`
- **Prior Knowledge**:
  - Module 1, Chapter 4 (URDF basics)
  - Chapter 5 (Digital Twin concepts)
  - Basic Linux file system navigation

:::note Hardware Requirements - Sim Mode
This chapter uses **Gazebo on a standard laptop** (CPU mode). No NVIDIA GPU required. Gazebo's physics runs efficiently on Intel/AMD CPUs with 4GB+ RAM.
:::

## Beyond Primitives: Using 3D Meshes

### Why Meshes Matter

**Primitive geometry** (boxes, cylinders, spheres) is great for prototyping, but production robots need **realistic visuals**:

| Geometry Type | Use Case | Example |
|---------------|----------|---------|
| **Box** | Collision detection | Robot base bounding box |
| **Cylinder** | Simple joints | Wheel, piston |
| **Mesh (.stl)** | Visual realism | Unitree Go2 body shell |
| **Mesh (.dae)** | Visual + Textures | Go2 with colors and decals |

### Mesh File Formats

| Format | Description | Use Case |
|--------|-------------|----------|
| **`.stl`** | Stereo Lithography (no colors) | 3D printing, collision |
| **`.dae`** | COLLADA (colors, textures) | Visual rendering |
| **`.obj`** | Wavefront (simple format) | Basic visualization |

:::info Best Practice
Use **`.stl` for collision geometry** (simpler = faster physics) and **`.dae` for visual geometry** (detailed = better rendering).
:::

### URDF Mesh Syntax

```xml
<visual>
  <geometry>
    <mesh filename="package://my_robot/meshes/body.dae" scale="1 1 1"/>
  </geometry>
</visual>

<collision>
  <geometry>
    <mesh filename="package://my_robot/meshes/body_collision.stl"/>
  </geometry>
</collision>
```

**Key points**:
- `package://` resolves to ROS 2 package path (e.g., `/opt/ros/humble/share/my_robot`)
- `scale` adjusts mesh size (1 1 1 = original size)
- Separate meshes for visual (detailed) and collision (simplified)

## Inertial Properties: Getting the Physics Right

### Why Inertia Matters

**Wrong inertia** → Robot tips over, joints oscillate, simulation crashes

**Correct inertia** → Realistic dynamics matching physical robot

### The Inertial Tag Structure

```xml
<inertial>
  <origin xyz="0 0 0.05" rpy="0 0 0"/>  <!-- Center of mass offset -->
  <mass value="12.5"/>                   <!-- Mass in kg -->
  <inertia ixx="0.1" ixy="0" ixz="0"    <!-- Inertia tensor -->
           iyy="0.15" iyz="0"
           izz="0.08"/>
</inertial>
```

### Calculating Inertia: Three Methods

#### Method 1: CAD Software (Recommended)
**Tools**: SolidWorks, Fusion 360, Onshape

**Steps**:
1. Import robot CAD model
2. Set material (e.g., Aluminum: 2700 kg/m³)
3. Run "Mass Properties" tool
4. Copy `ixx, iyy, izz` values directly

**Accuracy**: ✅ Exact (uses actual geometry)

#### Method 2: Online Calculators
**For primitive shapes only** (box, cylinder, sphere)

Example: Solid cylinder inertia
```
ixx = iyy = (1/12) * m * (3r² + h²)
izz = (1/2) * m * r²

where:
  m = mass (kg)
  r = radius (m)
  h = height (m)
```

**Accuracy**: ⚠️ Approximate (assumes uniform density)

#### Method 3: `meshlab` Tool
**For mesh files without CAD**

```bash
sudo apt install meshlab
meshlab body.stl
# Tools → Compute Geometric Measures → Inertia Tensor
```

**Accuracy**: ⚠️ Good (assumes uniform material)

:::caution Production Requirement
Always use **CAD software** for production URDFs. Wrong inertia can cause the simulated robot to behave unrealistically (e.g., Unitree Go2 flipping over when it should walk normally).
:::

## Advanced URDF: Unitree Go2 Leg Example

Let's build one leg of the Unitree Go2 with **meshes** and **accurate inertia**.

### File Structure
```
unitree_go2_description/
├── urdf/
│   └── go2_leg.urdf
├── meshes/
│   ├── hip_visual.dae       (detailed, with textures)
│   ├── hip_collision.stl    (simplified bounding box)
│   ├── thigh_visual.dae
│   ├── thigh_collision.stl
│   ├── shin_visual.dae
│   └── shin_collision.stl
└── package.xml
```

### Complete URDF with Meshes

```xml
<?xml version="1.0"?>
<robot name="go2_leg">

  <!-- BASE LINK (Body Attachment Point) -->
  <link name="base_link">
    <visual>
      <geometry>
        <box size="0.05 0.05 0.05"/>
      </geometry>
      <material name="black">
        <color rgba="0.1 0.1 0.1 1"/>
      </material>
    </visual>
  </link>

  <!-- HIP LINK -->
  <link name="hip_link">
    <visual>
      <geometry>
        <mesh filename="package://unitree_go2_description/meshes/hip_visual.dae"/>
      </geometry>
    </visual>
    <collision>
      <geometry>
        <mesh filename="package://unitree_go2_description/meshes/hip_collision.stl"/>
      </geometry>
    </collision>
    <inertial>
      <origin xyz="0.03 0 0" rpy="0 0 0"/>
      <mass value="0.696"/>  <!-- Actual Go2 hip mass -->
      <inertia ixx="0.00046" ixy="0" ixz="0"
               iyy="0.00046" iyz="0"
               izz="0.00046"/>
    </inertial>
  </link>

  <!-- HIP JOINT (Abduction: side-to-side movement) -->
  <joint name="hip_abduction_joint" type="revolute">
    <parent link="base_link"/>
    <child link="hip_link"/>
    <origin xyz="0 0.047 0" rpy="0 0 0"/>  <!-- 4.7cm offset -->
    <axis xyz="1 0 0"/>  <!-- Rotate around X-axis -->
    <limit lower="-0.802" upper="0.802" effort="23.7" velocity="30"/>
    <!-- Limits from Unitree specs: ±46°, 23.7 Nm torque, 30 rad/s speed -->
    <dynamics damping="0.1" friction="0.01"/>
  </joint>

  <!-- THIGH LINK -->
  <link name="thigh_link">
    <visual>
      <geometry>
        <mesh filename="package://unitree_go2_description/meshes/thigh_visual.dae"/>
      </geometry>
    </visual>
    <collision>
      <geometry>
        <mesh filename="package://unitree_go2_description/meshes/thigh_collision.stl"/>
      </geometry>
    </collision>
    <inertial>
      <origin xyz="0 0 -0.1" rpy="0 0 0"/>
      <mass value="1.013"/>  <!-- Actual Go2 thigh mass -->
      <inertia ixx="0.00552" ixy="0" ixz="0"
               iyy="0.00539" iyz="0"
               izz="0.00022"/>
    </inertial>
  </link>

  <!-- HIP FLEXION JOINT (Forward-backward swing) -->
  <joint name="hip_flexion_joint" type="revolute">
    <parent link="hip_link"/>
    <child link="thigh_link"/>
    <origin xyz="0.08 0 0" rpy="0 0 0"/>
    <axis xyz="0 1 0"/>  <!-- Rotate around Y-axis -->
    <limit lower="-1.047" upper="4.188" effort="23.7" velocity="30"/>
    <!-- Limits: -60° to +240°, 23.7 Nm, 30 rad/s -->
    <dynamics damping="0.1" friction="0.01"/>
  </joint>

  <!-- SHIN LINK -->
  <link name="shin_link">
    <visual>
      <geometry>
        <mesh filename="package://unitree_go2_description/meshes/shin_visual.dae"/>
      </geometry>
    </visual>
    <collision>
      <geometry>
        <mesh filename="package://unitree_go2_description/meshes/shin_collision.stl"/>
      </geometry>
    </collision>
    <inertial>
      <origin xyz="0 0 -0.1" rpy="0 0 0"/>
      <mass value="0.166"/>  <!-- Actual Go2 shin mass -->
      <inertia ixx="0.00081" ixy="0" ixz="0"
               iyy="0.00081" iyz="0"
               izz="0.00001"/>
    </inertial>
  </link>

  <!-- KNEE JOINT -->
  <joint name="knee_joint" type="revolute">
    <parent link="thigh_link"/>
    <child link="shin_link"/>
    <origin xyz="0 0 -0.2" rpy="0 0 0"/>
    <axis xyz="0 1 0"/>
    <limit lower="-2.697" upper="-0.916" effort="35.55" velocity="30"/>
    <!-- Limits: -154.5° to -52.5° (knee only bends one way), 35.55 Nm -->
    <dynamics damping="0.1" friction="0.01"/>
  </joint>

</robot>
```

### Key Improvements Over Basic URDF

| Feature | Basic URDF (Module 1) | Advanced URDF (This Chapter) |
|---------|----------------------|------------------------------|
| Visual Geometry | Primitive shapes | 3D meshes (`.dae`) with textures |
| Collision Geometry | Same as visual | Simplified meshes (`.stl`) for speed |
| Inertial Properties | Guessed values | Actual Unitree Go2 specs (kg, inertia tensor) |
| Joint Limits | Approximate | Exact (from hardware datasheets) |
| Dynamics | None | Damping + Friction coefficients |

## Adding Sensors: Gazebo Plugins

Sensors in URDF use **Gazebo plugins**—code modules that simulate hardware.

### Common Sensor Plugins

| Sensor | Plugin | ROS 2 Topic | Use Case |
|--------|--------|-------------|----------|
| **Camera** | `libgazebo_ros_camera.so` | `/camera/image_raw` | Vision, object detection |
| **Depth Camera** | `libgazebo_ros_camera.so` | `/camera/depth/image_raw` | 3D perception, SLAM |
| **Lidar** | `libgazebo_ros_ray_sensor.so` | `/scan` | Obstacle avoidance |
| **IMU** | `libgazebo_ros_imu_sensor.so` | `/imu` | Balance, orientation |

### Example: Adding a Camera to Go2

```xml
<link name="camera_link">
  <visual>
    <geometry>
      <box size="0.02 0.05 0.02"/>  <!-- Small box for camera -->
    </geometry>
    <material name="blue">
      <color rgba="0 0 0.8 1"/>
    </material>
  </visual>
  <collision>
    <geometry>
      <box size="0.02 0.05 0.02"/>
    </geometry>
  </collision>
  <inertial>
    <mass value="0.01"/>  <!-- 10 grams -->
    <inertia ixx="0.00001" ixy="0" ixz="0"
             iyy="0.00001" iyz="0"
             izz="0.00001"/>
  </inertial>
</link>

<joint name="camera_joint" type="fixed">
  <parent link="base_link"/>
  <child link="camera_link"/>
  <origin xyz="0.15 0 0.05" rpy="0 0 0"/>  <!-- 15cm forward, 5cm up -->
</joint>

<!-- Gazebo Plugin for Camera -->
<gazebo reference="camera_link">
  <sensor name="camera_sensor" type="camera">
    <update_rate>30</update_rate>  <!-- 30 FPS -->
    <camera>
      <horizontal_fov>1.57</horizontal_fov>  <!-- 90° field of view -->
      <image>
        <width>640</width>
        <height>480</height>
        <format>R8G8B8</format>  <!-- RGB -->
      </image>
      <clip>
        <near>0.1</near>  <!-- Min distance: 10cm -->
        <far>100</far>    <!-- Max distance: 100m -->
      </clip>
    </camera>
    <plugin name="camera_controller" filename="libgazebo_ros_camera.so">
      <ros>
        <namespace>/go2</namespace>
        <argument>--ros-args --remap camera:=camera/image_raw</argument>
      </ros>
      <camera_name>front_camera</camera_name>
      <frame_name>camera_link</frame_name>
    </plugin>
  </sensor>
</gazebo>
```

**What this does**:
1. Creates a `camera_link` (physical sensor location)
2. Gazebo plugin publishes images to `/go2/camera/image_raw`
3. Images are 640x480 @ 30 FPS (same as RealSense D435i specs)

:::tip Sim-to-Real Matching
Use the **same resolution and FPS** as your physical camera (e.g., RealSense D435i). This ensures algorithms tested in simulation work on real hardware without changes.
:::

## Using Xacro: URDF with Macros

**Problem**: URDF is verbose. A 4-legged robot has **4 identical legs**—copying XML 4 times is error-prone.

**Solution**: **Xacro** (XML Macros) lets you write reusable components.

### Basic Xacro Syntax

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="go2">

  <!-- Define a macro for one leg -->
  <xacro:macro name="leg" params="prefix">
    <link name="${prefix}_hip_link">
      <!-- ... -->
    </link>
    <joint name="${prefix}_hip_joint" type="revolute">
      <!-- ... -->
    </joint>
  </xacro:macro>

  <!-- Instantiate 4 legs -->
  <xacro:leg prefix="FL"/>  <!-- Front Left -->
  <xacro:leg prefix="FR"/>  <!-- Front Right -->
  <xacro:leg prefix="RL"/>  <!-- Rear Left -->
  <xacro:leg prefix="RR"/>  <!-- Rear Right -->

</robot>
```

### Converting Xacro to URDF

```bash
xacro go2.urdf.xacro > go2.urdf
```

**Benefits**:
- **DRY (Don't Repeat Yourself)**: Change one leg, update all 4
- **Parameters**: Adjust leg length, mass, etc. in one place
- **Conditionals**: Include/exclude sensors based on flags

:::info Production Standard
Real robot URDFs (Unitree, Boston Dynamics) use **Xacro** exclusively. Raw URDF is only for simple prototypes.
:::

## Sim-to-Real: Hardware Deployment

The URDF you create in this chapter is **hardware-agnostic**:

| Environment | Hardware | URDF Usage |
|-------------|----------|------------|
| **Gazebo Sim** | Laptop (CPU) | Full URDF with Gazebo plugins |
| **Isaac Sim** | Workstation (RTX GPU) | Same URDF, different physics engine |
| **Real Go2** | Jetson Orin (ARM) | URDF for `robot_state_publisher` (no Gazebo plugins) |

**Key insight**: The **same mesh files and joint parameters** work everywhere. Only the **simulation plugins** are disabled on real hardware.

:::caution Hardware Compatibility
Always verify joint limits match **physical hard stops**. If your URDF allows a knee to bend 360° but the real motor has a 135° limit, you'll **damage the hardware**!
:::

## Common Mistakes

### Mistake 1: Mesh File Not Found
```xml
<!-- ❌ Incorrect path -->
<mesh filename="meshes/hip.dae"/>
```
**Error**: `Resource not found: meshes/hip.dae`

**Fix**: Use `package://` URI:
```xml
<!-- ✅ Correct -->
<mesh filename="package://unitree_go2_description/meshes/hip.dae"/>
```

### Mistake 2: Collision Mesh Too Complex
```xml
<!-- ❌ Using detailed visual mesh for collision -->
<collision>
  <geometry>
    <mesh filename="package://my_robot/meshes/body_highres.dae"/>
    <!-- 100,000 polygons = very slow physics! -->
  </geometry>
</collision>
```

**Fix**: Use simplified mesh:
```xml
<!-- ✅ Simplified bounding box -->
<collision>
  <geometry>
    <box size="0.3 0.15 0.1"/>
  </geometry>
</collision>
```

### Mistake 3: Wrong Inertia Scale
```xml
<!-- ❌ Mass in grams instead of kg -->
<mass value="1500"/>  <!-- Should be 1.5 kg! -->
```

**Fix**: Always use **SI units** (kg, meters, radians).

## Summary

In this chapter, you learned:

✅ How to use **3D meshes** (`.stl`, `.dae`) for realistic visuals
✅ How to calculate **inertial properties** from CAD software
✅ Advanced URDF features: **dynamics** (damping, friction)
✅ How to add **Gazebo sensor plugins** (camera, lidar, IMU)
✅ **Xacro macros** for reusable robot components
✅ Sim-to-Real deployment: **same URDF** for Gazebo and real hardware
✅ Production best practices: **CAD-derived inertia**, **simplified collision meshes**

## What's Next?

In **Chapter 7: Gazebo Simulation**, you'll:
- Launch the Unitree Go2 URDF in Gazebo
- Control the robot with ROS 2 topics
- Test sensor data (camera, lidar) in simulation
- Run physics scenarios (walking, climbing stairs)

## Further Reading

- [URDF XML Specification](http://wiki.ros.org/urdf/XML)
- [Xacro Documentation](http://wiki.ros.org/xacro)
- [Gazebo Sensor Plugins](https://classic.gazebosim.org/tutorials?tut=ros_gzplugins)
- [Unitree Go2 Official URDF](https://github.com/unitreerobotics/unitree_ros2)

---

**Next Chapter**: [Chapter 7: Gazebo Simulation →](./chapter-7-gazebo-simulation.md)
