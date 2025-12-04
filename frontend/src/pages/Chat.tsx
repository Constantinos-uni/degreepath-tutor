import { useEffect, useState, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { part2Api, Student, ChatMessage } from "@/lib/api";
import { toast } from "@/hooks/use-toast";
import { Send, Bot, User, Loader2, Trash2, MessageSquare } from "lucide-react";

const PART2_BASE_URL = import.meta.env.VITE_PART2_API_URL || "http://localhost:8001";

export default function Chat() {
  const [students, setStudents] = useState<Student[]>([]);
  const [selectedStudent, setSelectedStudent] = useState<string>("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchStudents();
  }, []);

  useEffect(() => {
    if (selectedStudent) {
      fetchChatHistory();
    }
  }, [selectedStudent]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const fetchStudents = async () => {
    setLoading(true);
    try {
      const data = await part2Api.getStudents();
      setStudents(data);
      if (data.length > 0) {
        setSelectedStudent(data[0].student_id);
      }
    } catch {
      toast({ title: "Error", description: "Failed to fetch students", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const fetchChatHistory = async () => {
    try {
      const history = await part2Api.getChatHistory(selectedStudent);
      setMessages(history);
    } catch {
      setMessages([]);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || !selectedStudent) return;

    const userMessage = input;
    setInput("");
    setSending(true);
    setStreamingContent("");

    // Optimistically add user message
    setMessages((prev) => [...prev, { role: "student", content: userMessage, timestamp: new Date().toISOString() }]);

    try {
      // Use streaming endpoint
      const response = await fetch(`${PART2_BASE_URL}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student_id: selectedStudent, message: userMessage }),
      });

      if (!response.ok) {
        throw new Error("Chat request failed");
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let fullResponse = "";

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.content) {
                  fullResponse += data.content;
                  setStreamingContent(fullResponse);
                }
                if (data.done) {
                  // Streaming complete, add the full message
                  setMessages((prev) => [...prev, { 
                    role: "tutor", 
                    content: fullResponse, 
                    timestamp: data.timestamp || new Date().toISOString() 
                  }]);
                  setStreamingContent("");
                }
                if (data.error) {
                  throw new Error(data.error);
                }
              } catch (e) {
                // Ignore JSON parse errors for incomplete chunks
              }
            }
          }
        }
      }
    } catch {
      toast({ title: "Error", description: "Failed to send message", variant: "destructive" });
      // Remove optimistic message
      setMessages((prev) => prev.slice(0, -1));
      setStreamingContent("");
    } finally {
      setSending(false);
    }
  };

  const handleClearHistory = async () => {
    try {
      await part2Api.clearChatHistory(selectedStudent);
      setMessages([]);
      toast({ title: "Cleared", description: "Chat history cleared" });
    } catch {
      toast({ title: "Error", description: "Failed to clear history", variant: "destructive" });
    }
  };

  const currentStudent = students.find((s) => s.student_id === selectedStudent);

  return (
    <div className="flex h-[calc(100vh-3rem)] flex-col space-y-4 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI Tutor Chat</h1>
          <p className="text-muted-foreground">Get personalized academic guidance powered by LM Studio</p>
        </div>
      </div>

      <div className="grid flex-1 gap-4 lg:grid-cols-4">
        {/* Sidebar */}
        <Card className="border-border bg-card lg:col-span-1">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Select Student</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Select value={selectedStudent} onValueChange={setSelectedStudent}>
              <SelectTrigger>
                <SelectValue placeholder="Select student" />
              </SelectTrigger>
              <SelectContent>
                {students.map((student) => (
                  <SelectItem key={student.student_id} value={student.student_id}>
                    {student.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {currentStudent && (
              <div className="space-y-3 rounded-lg bg-secondary/50 p-3">
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Student ID</p>
                  <p className="font-mono text-sm">{currentStudent.student_id}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Degree</p>
                  <p className="text-sm">{currentStudent.degree}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Major</p>
                  <p className="text-sm">{currentStudent.major}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Completed</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {currentStudent.completed_units.map((u) => (
                      <span key={u} className="rounded bg-success/20 px-1.5 py-0.5 text-xs text-success">
                        {u}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}

            <Button variant="outline" size="sm" onClick={handleClearHistory} className="w-full gap-2">
              <Trash2 className="h-3 w-3" />
              Clear History
            </Button>
          </CardContent>
        </Card>

        {/* Chat Area */}
        <Card className="flex flex-col border-border bg-card lg:col-span-3">
          <CardHeader className="border-b border-border pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Bot className="h-5 w-5 text-primary" />
              DegreePath AI Tutor
            </CardTitle>
            <CardDescription>Ask questions about your degree, units, or study tips</CardDescription>
          </CardHeader>

          {/* Messages */}
          <CardContent className="flex-1 overflow-y-auto p-4 scrollbar-thin">
            {messages.length === 0 ? (
              <div className="flex h-full flex-col items-center justify-center text-center">
                <MessageSquare className="h-12 w-12 text-muted-foreground/30" />
                <p className="mt-4 font-medium">Start a conversation</p>
                <p className="text-sm text-muted-foreground">Ask about your units, prerequisites, or study strategies</p>
                <div className="mt-6 flex flex-wrap justify-center gap-2">
                  {[
                    "What have I completed?", 
                    "What should I take next?", 
                    "Tell me about COMP1010",
                    "What are the prerequisites for COMP3100?",
                    "Help me plan my study schedule",
                    "Explain the key concepts in AI",
                  ].map((q) => (
                    <button
                      key={q}
                      onClick={() => setInput(q)}
                      className="rounded-full bg-secondary px-3 py-1.5 text-xs text-secondary-foreground transition-colors hover:bg-secondary/80"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((msg, i) => (
                  <div
                    key={i}
                    className={`flex gap-3 ${msg.role === "student" ? "flex-row-reverse" : ""}`}
                  >
                    <div
                      className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                        msg.role === "student" ? "bg-primary" : "bg-secondary"
                      }`}
                    >
                      {msg.role === "student" ? (
                        <User className="h-4 w-4 text-primary-foreground" />
                      ) : (
                        <Bot className="h-4 w-4 text-secondary-foreground" />
                      )}
                    </div>
                    <div
                      className={`max-w-[80%] rounded-2xl px-4 py-2.5 ${
                        msg.role === "student"
                          ? "bg-primary text-primary-foreground"
                          : "bg-secondary text-secondary-foreground"
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  </div>
                ))}
                {/* Streaming response */}
                {sending && streamingContent && (
                  <div className="flex gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary">
                      <Bot className="h-4 w-4 text-secondary-foreground" />
                    </div>
                    <div className="max-w-[80%] rounded-2xl bg-secondary px-4 py-2.5 text-secondary-foreground">
                      <p className="text-sm whitespace-pre-wrap">{streamingContent}<span className="animate-pulse">▌</span></p>
                    </div>
                  </div>
                )}
                {/* Loading indicator when waiting for first token */}
                {sending && !streamingContent && (
                  <div className="flex gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-secondary">
                      <Loader2 className="h-4 w-4 animate-spin text-secondary-foreground" />
                    </div>
                    <div className="rounded-2xl bg-secondary px-4 py-2.5">
                      <p className="text-sm text-muted-foreground">Thinking...</p>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </CardContent>

          {/* Input */}
          <div className="border-t border-border p-4 space-y-3">
            {/* Quick prompts - always visible */}
            <div className="flex flex-wrap gap-1.5">
              {[
                "What should I take next?", 
                "Tell me about COMP2000",
                "Prerequisites for COMP3100?",
                "Help me plan my schedule",
              ].map((q) => (
                <button
                  key={q}
                  onClick={() => setInput(q)}
                  disabled={sending}
                  className="rounded-full bg-secondary/60 px-2.5 py-1 text-xs text-secondary-foreground transition-colors hover:bg-secondary disabled:opacity-50"
                >
                  {q}
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
                placeholder="Type your message..."
                disabled={!selectedStudent || sending}
                className="flex-1"
              />
              <Button onClick={handleSend} disabled={!selectedStudent || sending || !input.trim()}>
                {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
