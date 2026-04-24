import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error(`[ErrorBoundary] Error in section: ${this.props.sectionName || 'Unknown'}`, error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render() {
    if (this.state.hasError) {
      if (this.props.customFallback) {
        return this.props.customFallback(this.state.error, this.handleReset);
      }

      return (
        <div className="flex flex-col items-center justify-center p-6 bg-red-500/10 border border-red-500/30 rounded-2xl w-full h-full min-h-[150px]">
          <AlertTriangle className="w-8 h-8 text-red-400 mb-3" />
          <p className="text-red-300 text-sm font-medium mb-1 text-center">
            {this.props.fallback || 'Đã xảy ra lỗi trong quá trình hiển thị.'}
          </p>
          <button
            onClick={this.handleReset}
            className="mt-3 flex items-center gap-2 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg text-sm transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Thử lại
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
