import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { part2Api, Student } from "@/lib/api";
import { toast } from "@/hooks/use-toast";
import { Plus, User, GraduationCap, BookOpen, Loader2, MessageSquare, FileText } from "lucide-react";

export default function Students() {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newStudent, setNewStudent] = useState({
    student_id: "",
    name: "",
    degree: "Bachelor of Information Technology",
    major: "Software Development",
    completed_units: "",
    enrolled_units: "",
  });

  useEffect(() => {
    fetchStudents();
  }, []);

  const fetchStudents = async () => {
    setLoading(true);
    try {
      const data = await part2Api.getStudents();
      setStudents(data);
    } catch (error) {
      toast({ title: "Error", description: "Failed to fetch students. Is the API running?", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateStudent = async () => {
    setCreating(true);
    try {
      const student: Student = {
        student_id: newStudent.student_id,
        name: newStudent.name,
        degree: newStudent.degree,
        major: newStudent.major,
        completed_units: newStudent.completed_units.split(",").map((u) => u.trim()).filter(Boolean),
        enrolled_units: newStudent.enrolled_units.split(",").map((u) => u.trim()).filter(Boolean),
      };
      await part2Api.createStudent(student);
      toast({ title: "Success", description: `Student ${student.name} created!` });
      setDialogOpen(false);
      setNewStudent({
        student_id: "",
        name: "",
        degree: "Bachelor of Information Technology",
        major: "Software Development",
        completed_units: "",
        enrolled_units: "",
      });
      fetchStudents();
    } catch (error) {
      toast({ title: "Error", description: "Failed to create student", variant: "destructive" });
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Students</h1>
          <p className="text-muted-foreground">Manage student profiles and records</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="gap-2">
              <Plus className="h-4 w-4" />
              Add Student
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Create New Student</DialogTitle>
              <DialogDescription>Add a new student to the system</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="student_id">Student ID</Label>
                  <Input
                    id="student_id"
                    placeholder="e.g., s12345"
                    value={newStudent.student_id}
                    onChange={(e) => setNewStudent({ ...newStudent, student_id: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    placeholder="Full name"
                    value={newStudent.name}
                    onChange={(e) => setNewStudent({ ...newStudent, name: e.target.value })}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="degree">Degree</Label>
                <Input
                  id="degree"
                  value={newStudent.degree}
                  onChange={(e) => setNewStudent({ ...newStudent, degree: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="major">Major</Label>
                <Input
                  id="major"
                  value={newStudent.major}
                  onChange={(e) => setNewStudent({ ...newStudent, major: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="completed">Completed Units (comma-separated)</Label>
                <Input
                  id="completed"
                  placeholder="COMP1000, COMP1010"
                  value={newStudent.completed_units}
                  onChange={(e) => setNewStudent({ ...newStudent, completed_units: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="enrolled">Enrolled Units (comma-separated)</Label>
                <Input
                  id="enrolled"
                  placeholder="COMP1350, COMP2000"
                  value={newStudent.enrolled_units}
                  onChange={(e) => setNewStudent({ ...newStudent, enrolled_units: e.target.value })}
                />
              </div>
              <Button onClick={handleCreateStudent} disabled={creating} className="w-full">
                {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : "Create Student"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : students.length === 0 ? (
        <Card className="border-border bg-card">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <User className="h-12 w-12 text-muted-foreground/50" />
            <p className="mt-4 text-muted-foreground">No students found</p>
            <p className="text-sm text-muted-foreground">Create a new student or check if the API is running</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {students.map((student) => (
            <Card key={student.student_id} className="border-border bg-card transition-all hover:border-primary/50">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                    <User className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="text-base">{student.name}</CardTitle>
                    <CardDescription className="font-mono text-xs">{student.student_id}</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center gap-2 text-sm">
                  <GraduationCap className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">{student.degree}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <BookOpen className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">{student.major}</span>
                </div>
                <div className="space-y-1">
                  <p className="text-xs font-medium text-muted-foreground">Completed</p>
                  <div className="flex flex-wrap gap-1">
                    {student.completed_units.length > 0 ? (
                      student.completed_units.map((unit) => (
                        <span key={unit} className="rounded bg-success/10 px-2 py-0.5 text-xs font-medium text-success">
                          {unit}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-muted-foreground">None</span>
                    )}
                  </div>
                </div>
                <div className="space-y-1">
                  <p className="text-xs font-medium text-muted-foreground">Enrolled</p>
                  <div className="flex flex-wrap gap-1">
                    {student.enrolled_units.length > 0 ? (
                      student.enrolled_units.map((unit) => (
                        <span key={unit} className="rounded bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                          {unit}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-muted-foreground">None</span>
                    )}
                  </div>
                </div>
                <div className="flex gap-2 pt-2 border-t border-border">
                  <a
                    href={`/chat?student=${student.student_id}`}
                    className="flex-1 flex items-center justify-center gap-1 rounded-lg bg-primary/10 px-3 py-2 text-xs font-medium text-primary transition-colors hover:bg-primary/20"
                  >
                    <MessageSquare className="h-3 w-3" />
                    Chat
                  </a>
                  <a
                    href={`/reports?student=${student.student_id}`}
                    className="flex-1 flex items-center justify-center gap-1 rounded-lg bg-secondary px-3 py-2 text-xs font-medium text-secondary-foreground transition-colors hover:bg-secondary/80"
                  >
                    <FileText className="h-3 w-3" />
                    Reports
                  </a>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
