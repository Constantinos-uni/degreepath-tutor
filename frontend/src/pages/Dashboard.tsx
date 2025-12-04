import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";
import { part1Api, part2Api, HealthStatus } from "@/lib/api";
import { toast } from "@/hooks/use-toast";
import { Server, Cpu, Users, MessageSquare, Activity, Zap, FileText, Globe, Database, Brain, RefreshCw, Loader2 } from "lucide-react";

export default function Dashboard() {
  const [part1Status, setPart1Status] = useState<"online" | "offline" | "loading">("loading");
  const [part2Status, setPart2Status] = useState<"online" | "offline" | "loading">("loading");
  const [part2Health, setPart2Health] = useState<HealthStatus | null>(null);
  const [chatStats, setChatStats] = useState<{ 
    total_students: number; 
    total_messages: number; 
    active_conversations: number;
    discussed_units?: string[];
    discussed_topics?: string[];
    persistence_enabled?: boolean;
  } | null>(null);
  const [computingUnits, setComputingUnits] = useState<number>(0);
  const [refreshingRAG, setRefreshingRAG] = useState(false);

  useEffect(() => {
    checkHealth();
    loadComputingUnits();
  }, []);

  const checkHealth = async () => {
    setPart1Status("loading");
    setPart2Status("loading");

    try {
      await part1Api.health();
      setPart1Status("online");
    } catch {
      setPart1Status("offline");
    }

    try {
      const health = await part2Api.health();
      setPart2Status("online");
      setPart2Health(health);
      
      const stats = await part2Api.getChatStats();
      setChatStats(stats);
    } catch {
      setPart2Status("offline");
    }
  };

  const loadComputingUnits = async () => {
    try {
      const data = await part1Api.getComputingUnits();
      setComputingUnits(data.units.length);
    } catch {
      // Silent fail
    }
  };

  const handleRefreshRAG = async () => {
    setRefreshingRAG(true);
    try {
      const result = await part1Api.ingestLiveData();
      toast({ title: "RAG Refreshed", description: `Ingested ${result.units_ingested} units from live web` });
    } catch {
      toast({ title: "Error", description: "Failed to refresh RAG data", variant: "destructive" });
    } finally {
      setRefreshingRAG(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Monitor your DegreePath Tutor system status
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={handleRefreshRAG}
            disabled={refreshingRAG}
            variant="outline"
            className="gap-2"
          >
            {refreshingRAG ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Database className="h-4 w-4" />
            )}
            Refresh RAG
          </Button>
          <Button
            onClick={checkHealth}
            className="gap-2"
          >
            <Activity className="h-4 w-4" />
            Refresh Status
          </Button>
        </div>
      </div>

      {/* API Status Cards */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card className="border-border bg-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Part 1 API</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-2xl font-bold">Unit Database</p>
                <p className="text-xs text-muted-foreground">Port 8000 • Eligibility Engine</p>
              </div>
              <StatusBadge status={part1Status} />
            </div>
            <div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground">
              <div className="flex items-center gap-1">
                <Globe className="h-3 w-3 text-success" />
                Live Web Search
              </div>
              <div className="flex items-center gap-1">
                <Brain className="h-3 w-3 text-primary" />
                RAG Enabled
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border bg-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Part 2 API</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-2xl font-bold">AI Tutor</p>
                <p className="text-xs text-muted-foreground">
                  Port 8001 • {part2Health?.ai_backend || "LM Studio"}
                </p>
              </div>
              <StatusBadge status={part2Status} />
            </div>
            {part2Health && (
              <div className="mt-3 flex items-center gap-2">
                <Zap className={`h-3 w-3 ${part2Health.lm_studio ? "text-success" : "text-warning"}`} />
                <span className="text-xs text-muted-foreground">
                  {part2Health.lm_studio ? "AI Mode Active" : "Fallback Mode"}
                </span>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-border bg-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Students</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-gradient">{chatStats?.total_students || 0}</p>
            <p className="text-xs text-muted-foreground">Registered in system</p>
          </CardContent>
        </Card>

        <Card className="border-border bg-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Messages</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-gradient">{chatStats?.total_messages || 0}</p>
            <p className="text-xs text-muted-foreground">Total chat messages</p>
          </CardContent>
        </Card>

        <Card className="border-border bg-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active Chats</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-gradient">{chatStats?.active_conversations || 0}</p>
            <p className="text-xs text-muted-foreground">Active conversations</p>
          </CardContent>
        </Card>

        <Card className="border-border bg-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Computing Units</CardTitle>
            <Globe className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-gradient">{computingUnits}</p>
            <p className="text-xs text-muted-foreground">Live from Macquarie</p>
          </CardContent>
        </Card>
      </div>

      {/* Context & Persistence Info */}
      {chatStats?.persistence_enabled && (
        <Card className="border-border bg-card border-success/30">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Database className="h-4 w-4 text-success" />
              Context Persistence Active
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-2">Recently Discussed Units</p>
                <div className="flex flex-wrap gap-1">
                  {chatStats?.discussed_units?.length ? (
                    chatStats.discussed_units.map((unit) => (
                      <span key={unit} className="rounded bg-primary/10 px-2 py-0.5 text-xs font-mono text-primary">
                        {unit}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-muted-foreground">No units discussed yet</span>
                  )}
                </div>
              </div>
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-2">Recently Discussed Topics</p>
                <div className="flex flex-wrap gap-1">
                  {chatStats?.discussed_topics?.length ? (
                    chatStats.discussed_topics.map((topic) => (
                      <span key={topic} className="rounded bg-secondary px-2 py-0.5 text-xs text-secondary-foreground">
                        {topic}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-muted-foreground">No topics discussed yet</span>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick Actions */}
      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common tasks and shortcuts</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-5">
            <a
              href="/students"
              className="flex flex-col items-center gap-2 rounded-lg border border-border bg-secondary/50 p-4 text-center transition-colors hover:bg-secondary"
            >
              <Users className="h-6 w-6 text-primary" />
              <span className="text-sm font-medium">View Students</span>
            </a>
            <a
              href="/units"
              className="flex flex-col items-center gap-2 rounded-lg border border-border bg-secondary/50 p-4 text-center transition-colors hover:bg-secondary"
            >
              <Server className="h-6 w-6 text-primary" />
              <span className="text-sm font-medium">Lookup Unit</span>
            </a>
            <a
              href="/eligibility"
              className="flex flex-col items-center gap-2 rounded-lg border border-border bg-secondary/50 p-4 text-center transition-colors hover:bg-secondary"
            >
              <Activity className="h-6 w-6 text-primary" />
              <span className="text-sm font-medium">Check Eligibility</span>
            </a>
            <a
              href="/chat"
              className="flex flex-col items-center gap-2 rounded-lg border border-border bg-secondary/50 p-4 text-center transition-colors hover:bg-secondary"
            >
              <MessageSquare className="h-6 w-6 text-primary" />
              <span className="text-sm font-medium">AI Chat</span>
            </a>
            <a
              href="/reports"
              className="flex flex-col items-center gap-2 rounded-lg border border-border bg-secondary/50 p-4 text-center transition-colors hover:bg-secondary"
            >
              <FileText className="h-6 w-6 text-primary" />
              <span className="text-sm font-medium">AI Reports</span>
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
