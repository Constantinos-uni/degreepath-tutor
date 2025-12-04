import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { part2Api, Student, TutorReport } from "@/lib/api";
import { toast } from "@/hooks/use-toast";
import { FileText, Loader2, Sparkles, BookOpen, Lightbulb, Link as LinkIcon, Zap, Brain, Calendar, HelpCircle, CheckCircle, Globe, RefreshCw } from "lucide-react";

const loadingMessages = [
  "Fetching unit data from Macquarie...",
  "Analyzing curriculum with AI...",
  "Generating key concepts...",
  "Building study plan...",
  "Creating practice quizzes...",
  "Finding web resources...",
  "Finalizing report..."
];

export default function Reports() {
  const [students, setStudents] = useState<Student[]>([]);
  const [unitCode, setUnitCode] = useState("COMP1010");
  const [selectedStudent, setSelectedStudent] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [report, setReport] = useState<TutorReport | null>(null);

  useEffect(() => {
    fetchStudents();
  }, []);

  // Progress animation during loading
  useEffect(() => {
    if (loading) {
      const interval = setInterval(() => {
        setLoadingStep((prev) => (prev + 1) % loadingMessages.length);
      }, 2000);
      return () => clearInterval(interval);
    } else {
      setLoadingStep(0);
    }
  }, [loading]);

  const fetchStudents = async () => {
    try {
      const data = await part2Api.getStudents();
      setStudents(data);
    } catch {
      // Silent fail - students optional
    }
  };

  const handleGenerate = async () => {
    if (!unitCode.trim()) {
      toast({ title: "Error", description: "Please enter a unit code", variant: "destructive" });
      return;
    }

    setLoading(true);
    setReport(null);

    try {
      let data: TutorReport;
      if (selectedStudent) {
        data = await part2Api.generateTutorReport({ unit_code: unitCode, student_id: selectedStudent });
      } else {
        data = await part2Api.getTutorReport(unitCode);
      }
      setReport(data);
      toast({ title: "Success", description: "Report generated successfully!" });
    } catch (error) {
      toast({ title: "Error", description: "Failed to generate report. Make sure the API is running.", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty?.toLowerCase()) {
      case 'easy': return 'bg-green-500/10 text-green-500 border-green-500/20';
      case 'medium': return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
      case 'hard': return 'bg-red-500/10 text-red-500 border-red-500/20';
      default: return 'bg-gray-500/10 text-gray-500';
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">AI Study Reports</h1>
        <p className="text-muted-foreground flex items-center gap-2">
          <Globe className="h-4 w-4" />
          Generate comprehensive AI-powered study guides using LM Studio + Live Web Data
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-4">
        {/* Input Form */}
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              Generate Report
            </CardTitle>
            <CardDescription>Get personalized study guides for any unit</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="unit">Unit Code</Label>
              <Input
                id="unit"
                value={unitCode}
                onChange={(e) => setUnitCode(e.target.value.toUpperCase())}
                placeholder="COMP1010"
                className="font-mono"
              />
            </div>

            <div className="space-y-2">
              <Label>Student (optional)</Label>
              <Select value={selectedStudent || "none"} onValueChange={(val) => setSelectedStudent(val === "none" ? "" : val)}>
                <SelectTrigger>
                  <SelectValue placeholder="Generic report" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Generic (no student)</SelectItem>
                  {students.map((student) => (
                    <SelectItem key={student.student_id} value={student.student_id}>
                      {student.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                Select a student for personalized recommendations
              </p>
            </div>

            <Button onClick={handleGenerate} disabled={loading} className="w-full">
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-4 w-4" />
                  Generate Report
                </>
              )}
            </Button>

            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground">Quick Select</p>
              <div className="flex flex-wrap gap-2">
                {["COMP1000", "COMP1010", "COMP1350", "COMP2000", "COMP3100"].map((code) => (
                  <button
                    key={code}
                    onClick={() => setUnitCode(code)}
                    className="rounded bg-secondary px-2 py-1 text-xs font-mono text-secondary-foreground transition-colors hover:bg-secondary/80"
                  >
                    {code}
                  </button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Report Display */}
        <Card className="border-border bg-card lg:col-span-3">
          <CardHeader>
            <CardTitle>Generated Report</CardTitle>
            <CardDescription>AI-powered comprehensive study guide</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="relative">
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="h-24 w-24 rounded-full border-4 border-primary/20 border-t-primary animate-spin"></div>
                  </div>
                  <Brain className="h-12 w-12 text-primary relative z-10 m-6" />
                </div>
                <p className="mt-6 font-medium text-lg">Generating AI Report</p>
                <p className="text-sm text-primary animate-pulse mt-2">{loadingMessages[loadingStep]}</p>
                <p className="text-xs text-muted-foreground mt-4">This may take 30-60 seconds...</p>
                <div className="mt-4 flex gap-1">
                  {loadingMessages.map((_, i) => (
                    <div
                      key={i}
                      className={`h-1.5 w-6 rounded-full transition-all ${
                        i <= loadingStep ? 'bg-primary' : 'bg-muted'
                      }`}
                    />
                  ))}
                </div>
              </div>
            ) : !report ? (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <FileText className="h-16 w-16 text-muted-foreground/30" />
                <p className="mt-4 font-medium">No report generated</p>
                <p className="text-sm text-muted-foreground">Select a unit and click generate to create an AI study guide</p>
              </div>
            ) : (
              <div className="space-y-6 animate-slide-up">
                {/* Header */}
                <div className="flex items-start gap-4 pb-4 border-b">
                  <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary/60">
                    <BookOpen className="h-7 w-7 text-primary-foreground" />
                  </div>
                  <div className="flex-1">
                    <h2 className="text-2xl font-bold">{report.unit_code}</h2>
                    <p className="text-muted-foreground">{report.summary?.slice(0, 100)}...</p>
                    <div className="mt-2 flex items-center gap-2 flex-wrap">
                      <Badge className={getDifficultyColor(report.difficulty)}>
                        {report.difficulty?.toUpperCase()}
                      </Badge>
                      <Badge variant="outline" className="flex items-center gap-1">
                        <Zap className="h-3 w-3" />
                        AI Generated
                      </Badge>
                      <Badge variant="outline" className="flex items-center gap-1 text-success border-success/30">
                        <Globe className="h-3 w-3" />
                        Live Data
                      </Badge>
                    </div>
                  </div>
                  <Button variant="outline" size="sm" onClick={handleGenerate} disabled={loading}>
                    <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                  </Button>
                </div>

                {/* Tabs for different sections */}
                <Tabs defaultValue="summary" className="w-full">
                  <TabsList className="grid w-full grid-cols-6">
                    <TabsTrigger value="summary">Summary</TabsTrigger>
                    <TabsTrigger value="concepts">Concepts</TabsTrigger>
                    <TabsTrigger value="plan">Study Plan</TabsTrigger>
                    <TabsTrigger value="quizzes">Quizzes</TabsTrigger>
                    <TabsTrigger value="resources">Resources</TabsTrigger>
                    <TabsTrigger value="notes">Notes</TabsTrigger>
                  </TabsList>

                  <TabsContent value="summary" className="space-y-4 mt-4">
                    <div className="prose prose-sm max-w-none dark:prose-invert">
                      <p className="text-base leading-relaxed">{report.summary}</p>
                    </div>
                    <div>
                      <h3 className="flex items-center gap-2 text-sm font-semibold mb-3">
                        <Brain className="h-4 w-4 text-primary" />
                        Core Skills You'll Develop
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {report.core_skills?.map((skill, i) => (
                          <Badge key={i} variant="secondary" className="text-xs">
                            {skill}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </TabsContent>

                  <TabsContent value="concepts" className="space-y-4 mt-4">
                    <h3 className="flex items-center gap-2 text-sm font-semibold">
                      <Lightbulb className="h-4 w-4 text-yellow-500" />
                      Key Concepts to Master
                    </h3>
                    <div className="grid gap-3">
                      {report.key_concepts?.map((concept, i) => (
                        <Card key={i} className="bg-secondary/30">
                          <CardHeader className="pb-2">
                            <CardTitle className="text-base flex items-center gap-2">
                              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs text-primary-foreground">
                                {i + 1}
                              </span>
                              {concept.concept}
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <p className="text-sm text-muted-foreground">{concept.explain}</p>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </TabsContent>

                  <TabsContent value="plan" className="space-y-4 mt-4">
                    <h3 className="flex items-center gap-2 text-sm font-semibold">
                      <Calendar className="h-4 w-4 text-blue-500" />
                      4-Week Study Plan
                    </h3>
                    <div className="grid gap-4">
                      {report.study_plan?.map((week) => (
                        <Card key={week.week} className="bg-secondary/30">
                          <CardHeader className="pb-2">
                            <CardTitle className="text-base">Week {week.week}</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <ul className="space-y-2">
                              {week.tasks?.map((task, i) => (
                                <li key={i} className="flex items-start gap-2 text-sm">
                                  <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                                  <span>{task}</span>
                                </li>
                              ))}
                            </ul>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </TabsContent>

                  <TabsContent value="quizzes" className="space-y-4 mt-4">
                    <h3 className="flex items-center gap-2 text-sm font-semibold">
                      <HelpCircle className="h-4 w-4 text-purple-500" />
                      Practice Quizzes
                    </h3>
                    <div className="grid gap-4">
                      {report.quizzes?.map((quiz, i) => (
                        <Card key={i} className="bg-secondary/30">
                          <CardHeader className="pb-2">
                            <div className="flex items-start justify-between">
                              <CardTitle className="text-base">Question {i + 1}</CardTitle>
                              <Badge className={getDifficultyColor(quiz.difficulty)}>
                                {quiz.difficulty}
                              </Badge>
                            </div>
                          </CardHeader>
                          <CardContent className="space-y-3">
                            <p className="font-medium">{quiz.q}</p>
                            <details className="cursor-pointer group">
                              <summary className="text-primary font-semibold text-sm hover:underline">
                                Show Answer
                              </summary>
                              <p className="mt-2 pl-4 border-l-2 border-primary/30 text-sm text-muted-foreground">
                                {quiz.a}
                              </p>
                            </details>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </TabsContent>

                  <TabsContent value="resources" className="space-y-4 mt-4">
                    <h3 className="flex items-center gap-2 text-sm font-semibold">
                      <LinkIcon className="h-4 w-4 text-cyan-500" />
                      Recommended Resources (Web Search)
                    </h3>
                    <div className="grid gap-3 sm:grid-cols-2">
                      {report.public_resources?.map((resource, i) => (
                        <a
                          key={i}
                          href={resource.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="group flex flex-col gap-2 rounded-lg border border-border bg-card p-4 transition-all hover:border-primary/50 hover:shadow-md"
                        >
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="text-xs">
                              {resource.type}
                            </Badge>
                          </div>
                          <span className="font-medium group-hover:text-primary line-clamp-2">
                            {resource.title}
                          </span>
                          <p className="text-xs text-muted-foreground line-clamp-2">
                            {resource.why}
                          </p>
                        </a>
                      ))}
                    </div>
                  </TabsContent>

                  <TabsContent value="notes" className="space-y-4 mt-4">
                    <h3 className="flex items-center gap-2 text-sm font-semibold">
                      <Sparkles className="h-4 w-4 text-primary" />
                      Personalized Notes
                    </h3>
                    <Card className="bg-primary/5 border-primary/20">
                      <CardContent className="pt-4">
                        <p className="whitespace-pre-wrap text-sm">{report.student_specific_notes}</p>
                      </CardContent>
                    </Card>
                    {report.meta && (
                      <p className="text-xs text-muted-foreground">
                        Generated at: {new Date(report.meta.generated_at).toLocaleString()}
                      </p>
                    )}
                  </TabsContent>
                </Tabs>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
