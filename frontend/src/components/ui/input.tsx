import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  inputClassName?: string;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, inputClassName, type = "text", error, ...props }, ref) => {
    return (
      <div className={cn("w-full", className)}>
        <input
          type={type}
          className={cn(
            "flex h-9 w-full rounded-md border bg-background px-3 py-1 text-sm shadow-xs transition-colors",
            "placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50",
            "disabled:cursor-not-allowed disabled:opacity-50",
            error
              ? "border-destructive aria-invalid:border-destructive"
              : "border-input",
            inputClassName
          )}
          aria-invalid={!!error}
          ref={ref}
          {...props}
        />
        {error ? (
          <p className="mt-1 text-xs text-destructive">{error}</p>
        ) : null}
      </div>
    );
  }
);
Input.displayName = "Input";

export { Input };
