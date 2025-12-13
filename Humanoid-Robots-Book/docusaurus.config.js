// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

const lightCodeTheme = require('prism-react-renderer').themes.github;
const darkCodeTheme = require('prism-react-renderer').themes.dracula;

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Physical AI & Humanoid Robotics',
  tagline: 'Interactive Textbook with RAG-Powered Learning Assistant',
  favicon: 'img/favicon.ico',

  // Set the production url of your site here
  url: 'https://your-username.github.io',
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: '/Humanoid-Robots-Book/',

  // GitHub pages deployment config.
  organizationName: 'your-username', // Usually your GitHub org/user name.
  projectName: 'Humanoid-Robots-Book', // Usually your repo name.
  deploymentBranch: 'gh-pages',
  trailingSlash: false,

  // onBrokenLinks: 'throw',
  // onBrokenMarkdownLinks: 'warn',
  
  onBrokenLinks: 'warn', // <--- CHANGED THIS
  onBrokenMarkdownLinks: 'warn',

  // Even if you don't use internalization, you can use this field to set useful
  // metadata like html lang. For example, if your site is Chinese, you may want
  // to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'ur'],
    localeConfigs: {
      en: {
        label: 'English',
        direction: 'ltr',
        htmlLang: 'en-US',
      },
      ur: {
        label: 'اردو',
        direction: 'rtl',
        htmlLang: 'ur-PK',
      },
    },
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          routeBasePath: '/',
          sidebarPath: require.resolve('./sidebars.js'),
          editUrl: 'https://github.com/your-username/Humanoid-Robots-Book/tree/main/',
          showLastUpdateTime: true,
          remarkPlugins: [],
          rehypePlugins: [],
        },
        blog: false,
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      // Replace with your project's social card
      image: 'img/docusaurus-social-card.jpg',
      navbar: {
        title: 'Physical AI & Humanoid Robotics',
        logo: {
          alt: 'Physical AI Logo',
          src: 'img/logo.svg',
        },
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'tutorialSidebar',
            position: 'left',
            label: 'Textbook',
          },
          {
            type: 'localeDropdown',
            position: 'right',
          },
          {
            href: 'https://github.com/your-username/Humanoid-Robots-Book',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Modules',
            items: [
              {
                label: 'ROS 2 Basics',
                to: '/module-1-ros2-basics/chapter-1-intro',
              },
              {
                label: 'Digital Twin Development',
                to: '/module-2-digital-twin/chapter-5-digital-twin-intro',
              },
              {
                label: 'Isaac Gym & Sim',
                to: '/module-3-isaac/chapter-8-isaac-gym-intro',
              },
              {
                label: 'Vision-Language-Action',
                to: '/module-4-vla/chapter-11-vla-intro',
              },
            ],
          },
          {
            title: 'Resources',
            items: [
              {
                label: 'GitHub',
                href: 'https://github.com/your-username/Humanoid-Robots-Book',
              },
              {
                label: 'ROS 2 Documentation',
                href: 'https://docs.ros.org/en/humble/',
              },
              {
                label: 'Isaac Sim Docs',
                href: 'https://docs.omniverse.nvidia.com/isaacsim/',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} Physical AI & Humanoid Robotics. Built with Docusaurus.`,
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
        // additionalLanguages: ['python', 'bash', 'yaml', 'json', 'xml', 'urdf'],
      },
      colorMode: {
        defaultMode: 'light',
        disableSwitch: false,
        respectPrefersColorScheme: true,
      },
      docs: {
        sidebar: {
          hideable: true,
          autoCollapseCategories: true,
        },
      },
    }),

  plugins: [
    async function tailwindPlugin(context, options) {
      return {
        name: 'docusaurus-tailwindcss',
        configurePostCss(postcssOptions) {
          postcssOptions.plugins.push(require('tailwindcss'));
          postcssOptions.plugins.push(require('autoprefixer'));
          return postcssOptions;
        },
      };
    },
  ],

  scripts: [
    {
      src: '/js/chat-widget.js',
      async: true,
      defer: true,
    },
  ],

  stylesheets: [],
};

module.exports = config;
