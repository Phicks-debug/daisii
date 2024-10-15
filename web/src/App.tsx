import { useState, useRef, useEffect } from 'react';
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { Send, HelpCircle, RefreshCw, Upload } from "lucide-react"
import { Toaster } from "@/components/ui/toaster"
import { useToast } from "@/hooks/use-toast"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import ReactMarkdown from 'react-markdown';

function App() {
  const [messages, setMessages] = useState<{ text: string; isUser: boolean }[]>([]);
  const [isStreaming, setIsStreaming] = useState(false)
  const [input, setInput] = useState('');
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  // Auto-scroll to bottom whenever messages are updated
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (input.trim()) {
      // Add user's input to the message list
      setMessages(prevMessages => [...prevMessages, { text: input, isUser: true }]);
      const userInput = input;
      setInput('');
      
      try {
        const response = await fetch(`http://localhost:8001/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ role: "user", content: userInput }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (reader) {
          setIsStreaming(true);
          let fullResponse = '';

          // Add an initial empty AI response
          setMessages(prevMessages => [...prevMessages, { text: '', isUser: false }]);

          while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            fullResponse += chunk;

            // Update only the last message (AI's response)
            setMessages(prevMessages => [
              ...prevMessages.slice(0, -1),
              { text: fullResponse, isUser: false }
            ]);
          }
        }

      } catch (error) {
        console.error('Error:', error);
        toast({
          title: "Error",
          description: "An error occurred while processing your request.",
          variant: "destructive",
        });
      } finally {
        setIsStreaming(false);
      }
    }
  };

  const showHelp = () => {
    toast({
      title: "Help",
      description: "This is a AI chat application. Type your message and hit enter to chat with the Daisii.",
    });
  };

  const refreshChat = () => {
    setMessages([]);
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      toast({
        title: "File Uploaded",
        description: `${file.name} has been uploaded successfully.`,
      });
      // Here you would typically process the file, perhaps send it to a server
      // For now, we'll just add a message about the upload
      setMessages(prev => [...prev, { text: `File uploaded: ${file.name}`, isUser: true }]);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-sepia-100 to-sepia-200 dark:from-sepia-800 dark:to-sepia-900">
      
      {/* Small header with logo or Daisii text */}
      <header className="flex justify-between items-center p-1 dark:bg-sepia-700 text-center text-xl font-semibold">
        <span className="text-sepia-800 dark:text-sepia-200 pl-7p">Daisii</span>
        <div className="p-2 pr-2p">
          <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="bg-sepia-300/50 hover:bg-sepia-400/50">Menu</Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onClick={refreshChat}>
              <RefreshCw className="mr-2 h-4 w-4" />
              <span>New Chat</span>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={showHelp}>
              <HelpCircle className="mr-2 h-4 w-4" />
              <span>Help</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      <main className="flex-grow flex flex-col p-2 overflow-hidden items-center">
        {/* Chat display area */}
        <div
          ref={scrollAreaRef}
          className="flex-grow w-full max-w-2xl mx-auto p-2 overflow-y-auto custom-scrollbar"
        >
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex items-start mb-4 ${message.isUser ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex items-start space-x-2 ${message.isUser ? 'flex-row-reverse' : 'flex-row'}`}>
                <div
                  className={`p-3 rounded-lg ${
                    message.isUser ? 'bg-sepia-300 dark:bg-sepia-700 ml-auto' : 'bg-sepia-200 dark:bg-sepia-600 mr-auto'
                  }`}
                >
                  <ReactMarkdown>
                    {message.text}
                  </ReactMarkdown>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Chat input area */}
        <form onSubmit={handleSubmit} className="relative max-w-xl w-full flex justify-center mt-auto">
          <Textarea
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="bg-sepia-100/20 backdrop-blur-sm border-none focus:ring-2 focus:ring-sepia-500 pr-20 min-h-[40px] max-h-[120px] overflow-y-auto resize-none w-full"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
          />
          <div className="absolute right-1 bottom-1 flex">
            <Button
              type="button"
              size="icon"
              className="bg-sepia-400 hover:bg-sepia-500 mr-1"
              onClick={() => fileInputRef.current?.click()}
              disabled={isStreaming}
            >
              <Upload className="h-4 w-4" />
            </Button>
            <Button
              type="submit"
              size="icon"
              className="bg-sepia-500 hover:bg-sepia-600"
              disabled={isStreaming}
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".pdf,.docx,image/*"
            style={{ display: 'none' }}
            disabled={isStreaming}
          />
        </form>
      </main>

      <footer className="p-3 flex justify-center text-sm text-sepia-800 dark:text-sepia-200">
        <p>© 2024 TechXCorp. All right reserved.</p>
      </footer>

      <Toaster />
    </div>
  );
}

export default App;
