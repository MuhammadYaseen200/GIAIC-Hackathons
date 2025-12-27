/**
 * Root Component Wrapper for Docusaurus
 * Injects ChatWidget globally across all pages
 */

import React from 'react';
import ChatWidget from '@site/src/components/ChatWidget';

// ExecutionEnvironment is used to detect if we're running in browser
// This prevents SSR issues during build
import ExecutionEnvironment from '@docusaurus/ExecutionEnvironment';

interface RootProps {
  children: React.ReactNode;
}

const Root: React.FC<RootProps> = ({ children }) => {
  return (
    <>
      {children}
      {/* Only render ChatWidget on client-side (browser) */}
      {ExecutionEnvironment.canUseDOM && <ChatWidget />}
    </>
  );
};

export default Root;
