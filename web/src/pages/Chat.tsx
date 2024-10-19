import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { Send, HelpCircle, RefreshCw, Upload, LogOut, Copy, Check } from "lucide-react"
import { Toaster } from "@/components/ui/toaster"
import { useToast } from "@/hooks/use-toast"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { motion, AnimatePresence } from 'framer-motion';


const CodeBlock = ({ children }: { children: string }) => {
    const [isCopied, setIsCopied] = useState(false);
    const { toast } = useToast();

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(children);
            setIsCopied(true);
            toast({
                title: "Copied!",
                description: "Code copied to clipboard",
            });
            setTimeout(() => setIsCopied(false), 2000);
        } catch (err) {
            toast({
                title: "Failed to copy",
                description: "Please try again",
                variant: "destructive",
            });
        }
    };

    return (
        <div className="relative group">
            <Button
                size="icon"
                variant="outline"
                className="absolute right-2 top-2 h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity bg-sepia-200/80 dark:bg-sepia-700/80 hover:bg-sepia-300 dark:hover:bg-sepia-600"
                onClick={handleCopy}
            >
                <AnimatePresence mode="wait" initial={false}>
                    {isCopied ? (
                        <motion.div
                            key="check"
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            exit={{ scale: 0 }}
                            className="h-4 w-4 text-green-500"
                        >
                            <Check className="h-4 w-4" />
                        </motion.div>
                    ) : (
                        <motion.div
                            key="copy"
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            exit={{ scale: 0 }}
                        >
                            <Copy className="h-4 w-4" />
                        </motion.div>
                    )}
                </AnimatePresence>
            </Button>
            <code>{children}</code>
        </div>
    );
};


function App() {
    const [messages, setMessages] = useState<{ text: string; isUser: boolean }[]>([]);
    const [isStreaming, setIsStreaming] = useState(false)
    const [input, setInput] = useState('');
    const [isLoaded, setIsLoaded] = useState(false);
    const scrollAreaRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const { toast } = useToast();
    const navigate = useNavigate();

    useEffect(() => {
        // Add overflow-hidden to body during initial load
        document.body.style.overflow = 'hidden';

        // Trigger the loaded state after a small delay
        const timer = setTimeout(() => {
            setIsLoaded(true);
        }, 100);

        return () => clearTimeout(timer);
    }, []);

    // Auto-scroll to bottom whenever messages are updated
    useEffect(() => {
        if (scrollAreaRef.current) {
            scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
        }
    }, [messages]);

    const handleLogout = () => {
        localStorage.removeItem('isAuthenticated');
        localStorage.removeItem('token');
        toast({
            title: "Logged Out",
            description: "You have been successfully logged out.",
        });
        navigate('/');
    };


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
            description: "This is a AI chat application. Type your message and hit enter to chat with Daisii.",
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

    const containerVariants = {
        hidden: { opacity: 0, y: 20 },
        visible: {
            opacity: 1,
            y: 0,
            transition: {
                duration: 0.6,
                ease: "easeOut",
                staggerChildren: 0.1
            }
        }
    };

    const headerVariants = {
        hidden: { opacity: 0, y: -20 },
        visible: {
            opacity: 1,
            y: 0,
            transition: { duration: 0.5, ease: "easeOut" }
        }
    };

    const messageVariants = {
        hidden: { opacity: 0, x: 0, scale: 0.5 },
        visible: {
            opacity: 1,
            x: 0,
            scale: 1,
            transition: { duration: 0.3, ease: "easeOut" }
        }
    };

    const formVariants = {
        hidden: {
            opacity: 0,
            y: 20,
        },
        visible: {
            opacity: 1,
            y: 0,
            transition: {
                duration: 0.5,
                ease: "easeOut"
            }
        }
    };

    return (
        <div className="fixed inset-0 overflow-x-hidden main-scrollbar">
            <motion.div
                className="flex flex-col h-full bg-gradient-to-br from-sepia-100 to-sepia-200 dark:from-sepia-800 dark:to-sepia-900"
                initial="hidden"
                animate={isLoaded ? "visible" : "hidden"}
                variants={containerVariants}
            >

                {/* Small header with logo or Daisii text */}
                <motion.header
                    className="flex justify-between items-center p-1 dark:bg-sepia-700 text-center text-xl font-semibold"
                    variants={headerVariants}
                >
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
                                <DropdownMenuItem onClick={handleLogout} className="text-red-600 hover:text-red-700 focus:text-red-700">
                                    <LogOut className="mr-2 h-4 w-4" />
                                    <span>Logout</span>
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>
                </motion.header>

                {/* Main chat area */}
                <main className="flex-1 flex flex-col p-2 overflow-hidden items-center">

                    {/* Chat display area */}
                    <div
                        ref={scrollAreaRef}
                        className="flex-grow w-full max-w-2xl mx-auto p-2 overflow-y-auto overflow-x-hidden chat-container"
                    >
                        <AnimatePresence mode="sync">
                            {messages.map((message, index) => (
                                <motion.div
                                    key={index}
                                    className={`flex items-start mb-4 ${message.isUser ? 'justify-end' : 'justify-start'}`}
                                    variants={messageVariants}
                                    initial="hidden"
                                    animate="visible"
                                    custom={index}
                                >
                                    <div className={`flex items-start space-x-2 max-w-[95%] ${message.isUser ? 'flex-row-reverse' : 'flex-row'}`}>
                                        <div
                                            className={`p-3 rounded-lg w-full ${message.isUser ? 'bg-sepia-300 dark:bg-sepia-700' : 'bg-sepia-200 dark:bg-sepia-600'
                                                } prose dark:prose-invert`}
                                        >
                                            <div className='
                                                w-full overflow-hidden table-style
                                                [&>*]:w-full [&>*]:break-words
                                                [&>ul]:list-disc [&>ul]:ml-4 [&>ul]:pl-4
                                                [&>ol]:list-decimal [&>ol]:ml-4 [&>ol]:pl-4
                                                [&>h1]:text-2xl [&>h1]:font-bold [&>h1]:mb-4 [&>h1]:mt-2
                                                [&>h2]:text-xl [&>h2]:font-bold [&>h2]:mb-3 [&>h2]:mt-2
                                                [&>h3]:text-lg [&>h3]:font-bold [&>h3]:mb-2 [&>h3]:mt-2
                                                [&>p]:mb-0
                                                [&>blockquote]:border-l-4 [&>blockquote]:border-sepia-500 [&>blockquote]:pl-4 [&>blockquote]:italic [&>blockquote]:my-2
                                                [&>pre]:relative [&>pre]:bg-sepia-700/10 [&>pre]:p-2 [&>pre]:rounded [&>pre]:overflow-visible
                                                [&>pre>code]:block [&>pre>code]:overflow-x-auto 
                                                [&>pre>code]:pb-2
                                                [&>pre>code]:scrollbar [&>pre>code]:scrollbar-w-2 [&>pre>code]:scrollbar-h-2
                                                [&>pre>code]:scrollbar-thumb-[#D2B48C] hover:[&>pre>code]:scrollbar-thumb-[#B8860B]
                                                [&>pre>code]:scrollbar-track-transparent hover:[&>pre>code]:scrollbar-track-sepia-200/20
                                                [&>table]:min-w-full [&>table]:border-collapse [&>table]:my-4
                                                [&>table]:font-mono [&>table]:relative
                                                [&>table>thead]:bg-sepia-200/50 dark:[&>table>thead]:bg-sepia-600/30
                                                [&>table>thead>tr>th]:p-3 [&>table>thead>tr>th]:border-2
                                                [&>table>thead>tr>th]:border-sepia-700/60
                                                [&>table>thead>tr>th]:font-bold [&>table>thead>tr>th]:text-left
                                                [&>table>tbody>tr>td]:p-3 [&>table>tbody>tr>td]:border
                                                [&>table>tbody>tr>td]:border-sepia-400/30
                                                [&>table>tbody>tr:last-child>td]:border
                                                [&>table>tbody>tr>td:first-child]:font-semibold
                                                [&>table>tbody>tr]:transition-colors
                                                [&>table>tbody>tr:hover]:bg-sepia-300/20
                                                dark:[&>table>tbody>tr:hover]:bg-sepia-600/20
                                                [&>*>strong]:font-bold
                                                [&>*>em]:italic
                                                [&>*>del]:line-through
                                            '>
                                                <ReactMarkdown
                                                    remarkPlugins={[remarkGfm]}
                                                    components={{
                                                        code: ({ children }) => <CodeBlock>{children as string}</CodeBlock>,
                                                    }}
                                                >
                                                    {message.text}
                                                </ReactMarkdown>
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    </div>

                    {/* Chat input area */}
                    <motion.form
                        onSubmit={handleSubmit}
                        className="relative max-w-xl w-full flex justify-center mt-auto"
                        variants={formVariants}
                    >
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
                    </motion.form>
                </main>

                {/* Small footer for disclaimer of Daisii */}
                <motion.footer
                    className="p-3 flex justify-center text-sm text-sepia-800 dark:text-sepia-200"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.6, duration: 0.5 }}
                >
                    <p>© 2024 TechXCorp. All right reserved.</p>
                </motion.footer>

                <Toaster />
            </motion.div>
        </div>
    );
}


export default App;
