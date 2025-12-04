import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { part1Api } from "@/lib/api";
import { toast } from "@/hooks/use-toast";
import { CheckCircle, XCircle, Loader2, Shield, AlertTriangle, Globe } from "lucide-react";

interface EligibilityResult {
  eligible: boolean;
  missing_prerequisites: string[];
  incompatible_units: string[];
  errors: string[];
}

export default function Eligibility() {
  const [degree, setDegree] = useState("Bachelor of IT");
  const [completedUnits, setCompletedUnits] = useState("COMP1000");
  const [queryUnits, setQueryUnits] = useState("COMP1010");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<EligibilityResult | null>(null);
  const [targetUnit, setTargetUnit] = useState<string>("");

  const handleCheck = async () => {
    if (!queryUnits.trim()) {
      toast({ title: "Error", description: "Please enter units to check", variant: "destructive" });
      return;
    }

    setLoading(true);
    setResults(null);
    const target = queryUnits.split(",")[0].trim().toUpperCase();
    setTargetUnit(target);

    try {
      const data = await part1Api.checkEligibility({
        degree,
        completed_units: completedUnits.split(",").map((u) => u.trim()).filter(Boolean),
        query_units: queryUnits.split(",").map((u) => u.trim()).filter(Boolean),
      });
      // Handle both old and new response formats
      if ('eligible' in data) {
        setResults(data as EligibilityResult);
      } else {
        // Old format: { UNIT_CODE: true/false }
        const firstKey = Object.keys(data)[0];
        const isEligible = data[firstKey] as boolean;
        setResults({
          eligible: isEligible,
          missing_prerequisites: [],
          incompatible_units: [],
          errors: []
        });
      }
    } catch (error) {
      toast({ title: "Error", description: "Eligibility check failed. Is the API running?", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Eligibility Check</h1>
        <p className="text-muted-foreground">Verify if a student can enroll in specific units (uses live data)</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Input Form */}
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-primary" />
              Check Prerequisites
            </CardTitle>
            <CardDescription className="flex items-center gap-2">
              <Globe className="h-3 w-3" />
              Uses live web data from Macquarie University
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="degree">Degree Program</Label>
              <Input
                id="degree"
                value={degree}
                onChange={(e) => setDegree(e.target.value)}
                placeholder="Bachelor of IT"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="completed">Completed Units (comma-separated)</Label>
              <Input
                id="completed"
                value={completedUnits}
                onChange={(e) => setCompletedUnits(e.target.value.toUpperCase())}
                placeholder="COMP1000, COMP1010"
                className="font-mono"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="query">Unit to Check</Label>
              <Input
                id="query"
                value={queryUnits}
                onChange={(e) => setQueryUnits(e.target.value.toUpperCase())}
                placeholder="COMP2000"
                className="font-mono"
              />
            </div>
            <Button onClick={handleCheck} disabled={loading} className="w-full">
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Checking Live Data...
                </>
              ) : (
                <>
                  <Globe className="mr-2 h-4 w-4" />
                  Check Eligibility
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Results */}
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle>Results</CardTitle>
            <CardDescription>Eligibility status with detailed explanation</CardDescription>
          </CardHeader>
          <CardContent>
            {!results ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <Shield className="h-12 w-12 text-muted-foreground/30" />
                <p className="mt-4 text-sm text-muted-foreground">Enter details and click check to see results</p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Main result */}
                <div
                  className={`flex items-center justify-between rounded-lg p-4 ${
                    results.eligible ? "bg-success/10" : "bg-destructive/10"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {results.eligible ? (
                      <CheckCircle className="h-6 w-6 text-success" />
                    ) : (
                      <XCircle className="h-6 w-6 text-destructive" />
                    )}
                    <div>
                      <span className="font-mono font-medium text-lg">{targetUnit}</span>
                      <p className={`text-sm ${results.eligible ? "text-success" : "text-destructive"}`}>
                        {results.eligible ? "You are eligible to enroll" : "Not eligible yet"}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Missing Prerequisites */}
                {results.missing_prerequisites && results.missing_prerequisites.length > 0 && (
                  <div className="rounded-lg border border-warning/50 bg-warning/10 p-4">
                    <h4 className="flex items-center gap-2 font-medium text-warning mb-2">
                      <AlertTriangle className="h-4 w-4" />
                      Missing Prerequisites
                    </h4>
                    <p className="text-sm text-muted-foreground mb-3">
                      You need to complete these units first:
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {results.missing_prerequisites.map((prereq) => (
                        <span
                          key={prereq}
                          className="rounded-lg bg-warning/20 px-3 py-1.5 text-sm font-mono font-medium text-warning"
                        >
                          {prereq}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Incompatible Units */}
                {results.incompatible_units && results.incompatible_units.length > 0 && (
                  <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
                    <h4 className="flex items-center gap-2 font-medium text-destructive mb-2">
                      <XCircle className="h-4 w-4" />
                      Incompatible Units
                    </h4>
                    <p className="text-sm text-muted-foreground mb-3">
                      You have completed units that are incompatible:
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {results.incompatible_units.map((unit) => (
                        <span
                          key={unit}
                          className="rounded-lg bg-destructive/20 px-3 py-1.5 text-sm font-mono font-medium text-destructive"
                        >
                          {unit}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Success message */}
                {results.eligible && (
                  <div className="rounded-lg border border-success/50 bg-success/10 p-4">
                    <p className="text-sm text-success">
                      ✓ All prerequisites met. You can enroll in <span className="font-mono font-bold">{targetUnit}</span>!
                    </p>
                  </div>
                )}

                {/* Errors */}
                {results.errors && results.errors.length > 0 && (
                  <div className="rounded-lg border border-muted bg-muted/10 p-4">
                    <p className="text-sm text-muted-foreground">{results.errors.join(", ")}</p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Examples */}
      <Card className="border-border bg-card">
        <CardHeader>
          <CardTitle className="text-base">Quick Test Scenarios</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <button
              onClick={() => {
                setCompletedUnits("COMP1000");
                setQueryUnits("COMP1010");
              }}
              className="rounded-lg border border-border bg-secondary/30 p-3 text-left transition-colors hover:bg-secondary"
            >
              <p className="text-sm font-medium">✓ Should Pass</p>
              <p className="text-xs text-muted-foreground">COMP1000 → COMP1010</p>
            </button>
            <button
              onClick={() => {
                setCompletedUnits("");
                setQueryUnits("COMP1010");
              }}
              className="rounded-lg border border-border bg-secondary/30 p-3 text-left transition-colors hover:bg-secondary"
            >
              <p className="text-sm font-medium">✗ Should Fail</p>
              <p className="text-xs text-muted-foreground">Missing COMP1000 for COMP1010</p>
            </button>
            <button
              onClick={() => {
                setCompletedUnits("COMP1000, COMP1010");
                setQueryUnits("COMP3100");
              }}
              className="rounded-lg border border-border bg-secondary/30 p-3 text-left transition-colors hover:bg-secondary"
            >
              <p className="text-sm font-medium">✗ Advanced Unit</p>
              <p className="text-xs text-muted-foreground">Check COMP3100 prerequisites</p>
            </button>
            <button
              onClick={() => {
                setCompletedUnits("COMP1000, COMP1010, COMP2100, COMP2250, COMP2270");
                setQueryUnits("COMP3100");
              }}
              className="rounded-lg border border-border bg-secondary/30 p-3 text-left transition-colors hover:bg-secondary"
            >
              <p className="text-sm font-medium">✓ Ready for Y3</p>
              <p className="text-xs text-muted-foreground">All prereqs for COMP3100</p>
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
