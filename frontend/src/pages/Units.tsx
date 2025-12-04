import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { part1Api, UnitDetails, ComputingUnit, SmartSearchResult } from "@/lib/api";
import { toast } from "@/hooks/use-toast";
import { Search, BookOpen, AlertCircle, CheckCircle, XCircle, Loader2, Sparkles, RefreshCw, List } from "lucide-react";

export default function Units() {
  const [unitCode, setUnitCode] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [smartLoading, setSmartLoading] = useState(false);
  const [browseLoading, setBrowseLoading] = useState(false);
  const [unitData, setUnitData] = useState<UnitDetails | null>(null);
  const [smartResults, setSmartResults] = useState<SmartSearchResult | null>(null);
  const [allUnits, setAllUnits] = useState<ComputingUnit[]>([]);
  const [dataSource, setDataSource] = useState<string>("");

  // Load all computing units on mount
  useEffect(() => {
    loadAllUnits();
  }, []);

  const loadAllUnits = async () => {
    setBrowseLoading(true);
    try {
      const data = await part1Api.getComputingUnits();
      setAllUnits(data.units);
    } catch {
      // Silent fail - units browser is optional
    } finally {
      setBrowseLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!unitCode.trim()) {
      toast({ title: "Error", description: "Please enter a unit code", variant: "destructive" });
      return;
    }

    setLoading(true);
    setUnitData(null);
    setDataSource("");

    try {
      const data = await part1Api.getUnit(unitCode.toUpperCase());
      setUnitData(data);
      setDataSource("live"); // Backend uses live web search first
    } catch {
      toast({ title: "Not Found", description: `Unit ${unitCode} not found`, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const handleUnitClick = (code: string) => {
    setUnitCode(code);
    handleSearchWithCode(code);
  };

  const handleSearchWithCode = async (code: string) => {
    setLoading(true);
    setUnitData(null);
    setDataSource("");

    try {
      const data = await part1Api.getUnit(code);
      setUnitData(data);
      setDataSource("live"); // Backend uses live web search first
    } catch {
      toast({ title: "Not Found", description: `Unit ${code} not found`, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const handleSmartSearch = async () => {
    if (!searchQuery.trim()) {
      toast({ title: "Error", description: "Please enter a search query", variant: "destructive" });
      return;
    }

    setSmartLoading(true);
    setSmartResults(null);

    try {
      const results = await part1Api.smartSearch(searchQuery, true, true);
      setSmartResults(results);
    } catch {
      toast({ title: "Error", description: "Smart search failed", variant: "destructive" });
    } finally {
      setSmartLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Unit Lookup</h1>
        <p className="text-muted-foreground">Search for unit details, prerequisites, and learning outcomes</p>
      </div>

      <Tabs defaultValue="search" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3 lg:w-[400px]">
          <TabsTrigger value="search" className="gap-2">
            <Search className="h-4 w-4" />
            Code Search
          </TabsTrigger>
          <TabsTrigger value="smart" className="gap-2">
            <Sparkles className="h-4 w-4" />
            Smart Search
          </TabsTrigger>
          <TabsTrigger value="browse" className="gap-2">
            <List className="h-4 w-4" />
            Browse All
          </TabsTrigger>
        </TabsList>

        {/* Code Search Tab */}
        <TabsContent value="search" className="space-y-4">
          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5 text-primary" />
                Search by Unit Code
              </CardTitle>
              <CardDescription>Enter a unit code to view details (uses live data first)</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-3">
                <Input
                  placeholder="e.g., COMP1000"
                  value={unitCode}
                  onChange={(e) => setUnitCode(e.target.value.toUpperCase())}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  className="max-w-xs font-mono"
                />
                <Button onClick={handleSearch} disabled={loading}>
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Search className="h-4 w-4 mr-2" />Search</>}
                </Button>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {["COMP1000", "COMP1010", "COMP1350", "COMP2000", "COMP2300", "COMP3100", "COMP3850"].map((code) => (
                  <button
                    key={code}
                    onClick={() => handleUnitClick(code)}
                    className="rounded bg-secondary px-2 py-1 text-xs font-mono text-secondary-foreground transition-colors hover:bg-secondary/80"
                  >
                    {code}
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Smart Search Tab */}
        <TabsContent value="smart" className="space-y-4">
          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                Smart Search
              </CardTitle>
              <CardDescription>Search by topic, description, or keywords (combines RAG + Live data)</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-3">
                <Input
                  placeholder="e.g., machine learning, data structures, web development"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSmartSearch()}
                  className="flex-1"
                />
                <Button onClick={handleSmartSearch} disabled={smartLoading}>
                  {smartLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Sparkles className="h-4 w-4 mr-2" />Search</>}
                </Button>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {["machine learning", "database systems", "web development", "algorithms", "cybersecurity", "AI"].map((q) => (
                  <button
                    key={q}
                    onClick={() => setSearchQuery(q)}
                    className="rounded bg-primary/10 px-2 py-1 text-xs text-primary transition-colors hover:bg-primary/20"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Smart Search Results */}
          {smartResults && (
            <Card className="border-border bg-card animate-slide-up">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">
                    Found {smartResults.count} results for "{smartResults.query}"
                  </CardTitle>
                  <div className="flex gap-2">
                    {smartResults.sources_used.map((source) => (
                      <span
                        key={source}
                        className={`rounded px-2 py-0.5 text-xs font-medium ${
                          source === "live" ? "bg-success/20 text-success" : 
                          source === "rag" ? "bg-primary/20 text-primary" : 
                          "bg-secondary text-secondary-foreground"
                        }`}
                      >
                        {source}
                      </span>
                    ))}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {smartResults.results.map((result, i) => (
                    <button
                      key={i}
                      onClick={() => handleUnitClick(result.unit_code)}
                      className="w-full rounded-lg border border-border bg-secondary/30 p-4 text-left transition-colors hover:bg-secondary"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <p className="font-mono font-medium text-primary">{result.unit_code}</p>
                          <p className="text-sm">{result.title}</p>
                          {result.description && (
                            <p className="mt-1 text-xs text-muted-foreground line-clamp-2">{result.description}</p>
                          )}
                        </div>
                        <div className="flex flex-col items-end gap-1">
                          <span className={`rounded px-2 py-0.5 text-xs ${
                            result.source === "live" ? "bg-success/20 text-success" : "bg-secondary text-secondary-foreground"
                          }`}>
                            {result.source}
                          </span>
                          <span className="text-xs text-muted-foreground">{result.credit_points} CP</span>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Browse All Tab */}
        <TabsContent value="browse" className="space-y-4">
          <Card className="border-border bg-card">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <List className="h-5 w-5 text-primary" />
                    All Computing Units
                  </CardTitle>
                  <CardDescription>Browse all {allUnits.length} computing units from Macquarie University</CardDescription>
                </div>
                <Button variant="outline" size="sm" onClick={loadAllUnits} disabled={browseLoading}>
                  {browseLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {browseLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
              ) : allUnits.length === 0 ? (
                <p className="text-center text-muted-foreground py-8">No units loaded. Click refresh to load from live web.</p>
              ) : (
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {allUnits.map((unit) => (
                    <button
                      key={unit.code}
                      onClick={() => handleUnitClick(unit.code)}
                      className="rounded-lg border border-border bg-secondary/30 p-3 text-left transition-colors hover:bg-secondary hover:border-primary/50"
                    >
                      <p className="font-mono font-medium text-primary">{unit.code}</p>
                      <p className="text-xs text-muted-foreground line-clamp-2">{unit.title}</p>
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Results */}
      {unitData && (
        <Card className="border-border bg-card animate-slide-up">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg gradient-primary">
                <BookOpen className="h-6 w-6 text-primary-foreground" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <CardTitle className="text-xl">{unitData.unit_code}</CardTitle>
                  {dataSource && (
                    <span className={`rounded px-2 py-0.5 text-xs font-medium ${
                      dataSource === "live" ? "bg-success/20 text-success" : "bg-secondary text-secondary-foreground"
                    }`}>
                      {dataSource === "live" ? "🌐 Live" : "💾 Cached"}
                    </span>
                  )}
                </div>
                <CardDescription className="text-base">{unitData.details.title}</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Description */}
            {unitData.details.description && (
              <div className="rounded-lg bg-secondary/30 p-4">
                <p className="text-sm text-muted-foreground">{unitData.details.description}</p>
              </div>
            )}

            {/* Basic Info */}
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-lg bg-secondary/50 p-4">
                <p className="text-sm font-medium text-muted-foreground">Credit Points</p>
                <p className="text-2xl font-bold">{unitData.details.credit_points}</p>
              </div>
              <div className="rounded-lg bg-secondary/50 p-4">
                <p className="text-sm font-medium text-muted-foreground">Year Level</p>
                <p className="text-2xl font-bold">Year {unitData.details.year_level}</p>
              </div>
            </div>

            {/* Prerequisites */}
            <div className="space-y-2">
              <h3 className="flex items-center gap-2 text-sm font-medium">
                <CheckCircle className="h-4 w-4 text-success" />
                Prerequisites
              </h3>
              <div className="flex flex-wrap gap-2">
                {unitData.details.prerequisites.length > 0 ? (
                  unitData.details.prerequisites.map((prereq) => (
                    <button 
                      key={prereq} 
                      onClick={() => handleUnitClick(prereq)}
                      className="rounded-lg bg-success/10 px-3 py-1 text-sm font-medium text-success hover:bg-success/20 transition-colors"
                    >
                      {prereq}
                    </button>
                  ))
                ) : (
                  <span className="text-sm text-muted-foreground">No prerequisites</span>
                )}
              </div>
            </div>

            {/* Corequisites */}
            {unitData.details.corequisites.length > 0 && (
              <div className="space-y-2">
                <h3 className="flex items-center gap-2 text-sm font-medium">
                  <AlertCircle className="h-4 w-4 text-warning" />
                  Corequisites
                </h3>
                <div className="flex flex-wrap gap-2">
                  {unitData.details.corequisites.map((coreq) => (
                    <button
                      key={coreq}
                      onClick={() => handleUnitClick(coreq)}
                      className="rounded-lg bg-warning/10 px-3 py-1 text-sm font-medium text-warning hover:bg-warning/20 transition-colors"
                    >
                      {coreq}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Incompatible Units */}
            {unitData.details.incompatible_units.length > 0 && (
              <div className="space-y-2">
                <h3 className="flex items-center gap-2 text-sm font-medium">
                  <XCircle className="h-4 w-4 text-destructive" />
                  Incompatible Units
                </h3>
                <div className="flex flex-wrap gap-2">
                  {unitData.details.incompatible_units.map((unit) => (
                    <span key={unit} className="rounded-lg bg-destructive/10 px-3 py-1 text-sm font-medium text-destructive">
                      {unit}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Learning Outcomes */}
            {unitData.details.learning_outcomes.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-sm font-medium">Learning Outcomes</h3>
                <ul className="space-y-2">
                  {unitData.details.learning_outcomes.map((outcome, i) => (
                    <li key={i} className="flex gap-3 text-sm text-muted-foreground">
                      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-medium text-primary">
                        {i + 1}
                      </span>
                      {outcome}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
