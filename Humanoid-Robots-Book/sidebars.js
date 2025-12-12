/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */

// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  // Main tutorial sidebar
  tutorialSidebar: [
    {
      type: 'doc',
      id: 'intro',
      label: 'Introduction',
    },
    {
      type: 'category',
      label: 'Module 1: ROS 2 Basics & Nervous System',
      collapsed: false,
      items: [
        {
          type: 'doc',
          id: 'module-1-ros2-basics/chapter-1-intro',
          label: 'Ch 1: Introduction to ROS 2',
        },
        {
          type: 'doc',
          id: 'module-1-ros2-basics/chapter-2-pub-sub',
          label: 'Ch 2: Pub-Sub Communication',
        },
        {
          type: 'doc',
          id: 'module-1-ros2-basics/chapter-3-services-actions',
          label: 'Ch 3: Services & Actions',
        },
        {
          type: 'doc',
          id: 'module-1-ros2-basics/chapter-4-nervous-system',
          label: 'Ch 4: Robotic Nervous System',
        },
      ],
    },
    {
      type: 'category',
      label: 'Module 2: Digital Twin Development',
      collapsed: true,
      items: [
        {
          type: 'doc',
          id: 'module-2-digital-twin/chapter-5-digital-twin-intro',
          label: 'Ch 5: Digital Twin Introduction',
        },
        {
          type: 'doc',
          id: 'module-2-digital-twin/chapter-6-urdf-modeling',
          label: 'Ch 6: URDF Modeling',
        },
        {
          type: 'doc',
          id: 'module-2-digital-twin/chapter-7-gazebo-simulation',
          label: 'Ch 7: Gazebo Simulation',
        },
      ],
    },
    {
      type: 'category',
      label: 'Module 3: Isaac Gym & Sim',
      collapsed: true,
      items: [
        {
          type: 'doc',
          id: 'module-3-isaac/chapter-8-isaac-gym-intro',
          label: 'Ch 8: Isaac Gym Introduction',
        },
        {
          type: 'doc',
          id: 'module-3-isaac/chapter-9-rl-training',
          label: 'Ch 9: RL Training Pipelines',
        },
        {
          type: 'doc',
          id: 'module-3-isaac/chapter-10-sim-to-real',
          label: 'Ch 10: Sim-to-Real Transfer',
        },
      ],
    },
    {
      type: 'category',
      label: 'Module 4: Vision-Language-Action Models',
      collapsed: true,
      items: [
        {
          type: 'doc',
          id: 'module-4-vla/chapter-11-vla-intro',
          label: 'Ch 11: VLA Introduction',
        },
        {
          type: 'doc',
          id: 'module-4-vla/chapter-12-multimodal-integration',
          label: 'Ch 12: Multimodal Integration',
        },
        {
          type: 'doc',
          id: 'module-4-vla/chapter-13-deployment',
          label: 'Ch 13: Deployment Strategies',
        },
      ],
    },
    {
      type: 'category',
      label: 'Appendices',
      collapsed: true,
      items: [
        {
          type: 'doc',
          id: 'appendix/glossary',
          label: 'Glossary',
        },
        {
          type: 'doc',
          id: 'appendix/resources',
          label: 'Additional Resources',
        },
        {
          type: 'doc',
          id: 'appendix/troubleshooting',
          label: 'Troubleshooting Guide',
        },
      ],
    },
  ],
};

module.exports = sidebars;
