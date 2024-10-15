import { useState, useRef, useEffect } from 'react';
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Send, HelpCircle, RefreshCw, Upload } from "lucide-react"
import { Toaster } from "@/components/ui/toaster"
import { useToast } from "@/hooks/use-toast"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

function App() {
  const [messages, setMessages] = useState<{ text: string; isUser: boolean }[]>([]);
  const [input, setInput] = useState('');
  const [isInputCentered, setIsInputCentered] = useState(true);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      setMessages([...messages, { text: input, isUser: true }]);
      setInput('');
      setIsInputCentered(false);
      // Simulate bot response
      setTimeout(() => {
        setMessages(prev => [...prev, { text: "I'm a smart AI assistant. How can I help you?", isUser: false }]);
      }, 1000);
    }
  };

  const showHelp = () => {
    toast({
      title: "Help",
      description: "This is a futuristic chat application. Type your message and hit enter to chat with the AI.",
    });
  };

  const refreshChat = () => {
    setMessages([]);
    setIsInputCentered(true);
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
      <nav className="p-4 flex justify-end">
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
      </nav>

      <main className="flex-grow flex flex-col p-4 overflow-hidden">
        <ScrollArea className="flex-grow mb-4 rounded-lg bg-sepia-50/10 backdrop-blur-md" ref={scrollAreaRef}>
          <div className="p-4 space-y-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`p-3 rounded-lg ${
                  message.isUser
                    ? 'bg-sepia-300 dark:bg-sepia-700 ml-auto'
                    : 'bg-sepia-200 dark:bg-sepia-600 mr-auto'
                } max-w-[80%]`}
              >
                {message.text}
              </div>
            ))}
          </div>
        </ScrollArea>

        <form onSubmit={handleSubmit} className={`relative ${isInputCentered ? 'mx-auto w-2/3' : 'w-full'}`}>
          <Textarea
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="bg-sepia-100/20 backdrop-blur-sm border-none focus:ring-2 focus:ring-sepia-500 pr-20 min-h-[40px] max-h-[120px] overflow-y-auto resize-none"
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
            >
              <Upload className="h-4 w-4" />
            </Button>
            <Button type="submit" size="icon" className="bg-sepia-500 hover:bg-sepia-600">
              <Send className="h-4 w-4" />
            </Button>
          </div>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".pdf,.docx,image/*"
            style={{ display: 'none' }}
          />
        </form>
      </main>

      <footer className="p-4 flex justify-center text-sm text-sepia-800 dark:text-sepia-200">
        <p>© 2023 FutureTalk AI. All rights reserved.</p>
      </footer>

      <Toaster />
    </div>
  );
}

export default App;