import { useState, useEffect } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
import { Toaster } from "@/components/ui/toaster";

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();
  const location = useLocation();

  useEffect(() => {
    // Show welcome message if user just registered
    if (location.state?.registered) {
      toast({
        title: "Welcome!",
        description: "Your account has been created. Please login.",
      });
      // Clear the state
      navigate('/', { replace: true });
    }
  }, [location, toast, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const response = await fetch(`http://localhost:8001/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        // Store the token or user data as needed
        localStorage.setItem('token', data.token);
        localStorage.setItem('isAuthenticated', 'true');

        toast({
          title: "Success",
          description: "Login successful!",
        });
        navigate('/chat');
      } else {
        const data = await response.json();
        throw new Error(data.message || 'Invalid credentials');
      }
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Login failed",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-sepia-100 to-sepia-200 dark:from-sepia-800 dark:to-sepia-900">
      <header className="flex justify-center items-center p-1 dark:bg-sepia-700 text-center text-xl font-semibold">
        <span className="text-sepia-800 dark:text-sepia-200">Daisii</span>
      </header>

      <main className="flex-grow flex items-center justify-center p-4">
        <div className="w-full max-w-md p-8 bg-sepia-100/70 backdrop-blur-sm rounded-lg shadow-lg">
          <h2 className="text-2xl font-bold text-center mb-6 text-sepia-800 dark:text-sepia-200">
            Who are you?
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Input
                type="text"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-sepia-100/20 border-sepia-300"
                disabled={isLoading}
                required
              />
            </div>

            <div>
              <Input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-sepia-100/20 border-sepia-300"
                disabled={isLoading}
                required
              />
            </div>

            <Button
              type="submit"
              className="w-full bg-sepia-500 hover:bg-sepia-600 text-white"
              disabled={isLoading}
            >
              {isLoading ? 'Logging in...' : 'Sign In'}
            </Button>

            <div className="text-center text-sm text-sepia-700 dark:text-sepia-300">
              Don't have an account?{' '}
              <Link to="/register" className="text-sepia-800 dark:text-sepia-200 underline hover:text-sepia-600">
                Register here
              </Link>
            </div>
          </form>
        </div>
      </main>

      <footer className="p-3 flex justify-center text-sm text-sepia-800 dark:text-sepia-200">
        <p>© 2024 TechXCorp. All rights reserved.</p>
      </footer>

      <Toaster />
    </div>
  );
}