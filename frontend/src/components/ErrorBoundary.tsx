import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
    children: ReactNode;
    fallback?: React.ComponentType<{ error: Error; resetErrorBoundary: () => void }>;
    onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('Uncaught error:', error, errorInfo);
        this.props.onError?.(error, errorInfo);
    }

    private resetErrorBoundary = () => {
        this.setState({ hasError: false, error: null });
    };

    public render() {
        if (this.state.hasError && this.state.error) {
            const FallbackComponent = this.props.fallback;
            
            if (FallbackComponent) {
                return <FallbackComponent error={this.state.error} resetErrorBoundary={this.resetErrorBoundary} />;
            }
            
            return (
                <div className="alert alert-danger m-3">
                    <h2>Something went wrong.</h2>
                    <details style={{ whiteSpace: 'pre-wrap' }}>
                        {this.state.error.toString()}
                    </details>
                    <button 
                        type="button" 
                        className="btn btn-primary mt-2"
                        onClick={this.resetErrorBoundary}
                    >
                        Try again
                    </button>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;