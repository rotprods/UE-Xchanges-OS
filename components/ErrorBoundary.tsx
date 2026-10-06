"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught:", error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[200px] p-6 border border-[rgba(255,0,85,0.3)] bg-[rgba(5,15,25,0.6)] backdrop-blur-md rounded-2xl space-y-4">
          <div className="w-10 h-10 border-2 border-[#FF0055] rounded-full flex items-center justify-center">
            <span className="text-[#FF0055] text-xl font-bold">!</span>
          </div>
          <h3 className="font-orbitron text-[#FF0055] text-sm font-bold tracking-wider">
            {this.props.fallbackTitle || "MODULE CRASHED"}
          </h3>
          <p className="font-mono text-[10px] text-[rgba(255,255,255,0.4)] text-center max-w-xs">
            {this.state.error?.message || "An unexpected error occurred"}
          </p>
          <button
            onClick={this.handleRetry}
            className="px-4 py-2 border border-[#00F0FF] text-[#00F0FF] font-orbitron text-[10px] font-bold rounded-lg hover:bg-[rgba(0,240,255,0.1)] transition-all"
          >
            RETRY
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
