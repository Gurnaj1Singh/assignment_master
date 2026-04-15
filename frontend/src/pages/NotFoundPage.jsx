import { useNavigate } from 'react-router-dom'
import { FileQuestion, ArrowLeft, Home } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function NotFoundPage() {
  const navigate = useNavigate()

  return (
    <div className="flex min-h-screen flex-col items-center justify-center text-center px-4 bg-background">
      <FileQuestion className="h-16 w-16 text-muted-foreground mb-6" />
      <h1 className="text-4xl font-bold tracking-tight">404</h1>
      <p className="text-lg text-muted-foreground mt-2">Page not found</p>
      <p className="text-sm text-muted-foreground mt-1 max-w-md">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <div className="flex gap-3 mt-8">
        <Button variant="outline" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Go Back
        </Button>
        <Button onClick={() => navigate('/')}>
          <Home className="h-4 w-4 mr-2" />
          Home
        </Button>
      </div>
    </div>
  )
}
