import { cn } from "@/lib/utils";

interface StatusBadgeProps {
  status: "online" | "offline" | "loading";
  label?: string;
  className?: string;
}

export function StatusBadge({ status, label, className }: StatusBadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium",
        status === "online" && "bg-success/10 text-success",
        status === "offline" && "bg-destructive/10 text-destructive",
        status === "loading" && "bg-warning/10 text-warning",
        className
      )}
    >
      <span
        className={cn(
          "h-2 w-2 rounded-full",
          status === "online" && "bg-success animate-pulse",
          status === "offline" && "bg-destructive",
          status === "loading" && "bg-warning animate-pulse"
        )}
      />
      {label || (status === "online" ? "Online" : status === "offline" ? "Offline" : "Loading")}
    </div>
  );
}
