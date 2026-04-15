import { Component } from 'react'
import { AlertTriangle, RotateCcw } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-[60vh] flex-col items-center justify-center text-center px-4">
          <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
          <h2 className="text-xl font-bold">Something went wrong</h2>
          <p className="text-sm text-muted-foreground mt-2 max-w-md">
            An unexpected error occurred. Try refreshing the page or going back.
          </p>
          {this.state.error?.message && (
            <pre className="mt-3 max-w-lg rounded-md bg-muted px-4 py-2 text-xs text-muted-foreground overflow-auto">
              {this.state.error.message}
            </pre>
          )}
          <div className="flex gap-3 mt-6">
            <Button variant="outline" onClick={this.handleReset}>
              <RotateCcw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
            <Button onClick={() => (window.location.href = '/')}>
              Go Home
            </Button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
