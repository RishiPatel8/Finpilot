import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught React Error caught by ErrorBoundary:', error, errorInfo);
    this.setState({ errorInfo });
  }

  public handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen bg-[#F6F8FC] flex items-center justify-center p-6 text-[#172033] font-['Plus_Jakarta_Sans',sans-serif]">
          <div className="max-w-md w-full bg-white border border-[#E6EAF0] rounded-2xl p-6 shadow-lg text-center space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-[#FFF5F6] border border-[#D9485F]/20 text-[#D9485F] mx-auto flex items-center justify-center">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-base font-bold text-[#172033]">Something went wrong</h2>
              <p className="text-xs text-[#697386] mt-1">
                An unexpected UI rendering error occurred. FinPilot prevented an unhandled app crash.
              </p>
            </div>
            {this.state.error && (
              <div className="p-3 bg-[#F6F8FC] rounded-xl text-left border border-[#E6EAF0] max-h-40 overflow-y-auto">
                <p className="text-[11px] font-mono font-bold text-[#D9485F]">
                  {this.state.error.name}: {this.state.error.message}
                </p>
                {this.state.errorInfo?.componentStack && (
                  <pre className="text-[10px] text-[#697386] mt-1 font-mono whitespace-pre-wrap">
                    {this.state.errorInfo.componentStack}
                  </pre>
                )}
              </div>
            )}
            <button
              onClick={this.handleReset}
              className="inline-flex items-center gap-2 px-4 py-2 bg-[#6478E8] hover:bg-[#5063D8] text-white rounded-xl text-xs font-semibold shadow-sm transition-all"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Reload Application
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
