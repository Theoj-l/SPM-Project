"use client";

import * as React from "react";
import { ChevronDownIcon } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

interface DatePickerProps {
  value?: Date;
  onChange?: (date: Date | undefined) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  id?: string;
  showTime?: boolean;
}

export function DatePicker({
  value,
  onChange,
  placeholder = "Select date",
  disabled = false,
  className,
  id,
  showTime = false,
}: DatePickerProps) {
  const [open, setOpen] = React.useState(false);

  const handleDateSelect = (date: Date | undefined) => {
    if (date && value) {
      // Preserve the time when changing date
      const newDateTime = new Date(
        date.getFullYear(),
        date.getMonth(),
        date.getDate(),
        value.getHours(),
        value.getMinutes()
      );
      onChange?.(newDateTime);
    } else {
      onChange?.(date);
    }
    setOpen(false);
  };

  const handleTimeChange = (timeString: string) => {
    if (value && timeString) {
      const [hours, minutes] = timeString.split(":");
      const newDateTime = new Date(
        value.getFullYear(),
        value.getMonth(),
        value.getDate(),
        parseInt(hours),
        parseInt(minutes)
      );
      onChange?.(newDateTime);
    }
  };

  if (showTime) {
    return (
      <div className="flex gap-2">
        <Popover open={open} onOpenChange={setOpen}>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              id={id}
              className={cn(
                "flex-1 justify-between font-normal",
                !value && "text-muted-foreground",
                className
              )}
              disabled={disabled}
            >
              {value ? value.toLocaleDateString() : placeholder}
              <ChevronDownIcon className="h-4 w-4" />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto overflow-hidden p-0" align="start">
            <Calendar
              mode="single"
              selected={value}
              captionLayout="dropdown"
              onSelect={handleDateSelect}
              disabled={(date) =>
                date < new Date(new Date().setHours(0, 0, 0, 0))
              }
            />
          </PopoverContent>
        </Popover>
        <Input
          type="time"
          value={value ? value.toTimeString().slice(0, 5) : ""}
          onChange={(e) => handleTimeChange(e.target.value)}
          className="w-32"
          disabled={disabled}
        />
      </div>
    );
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          id={id}
          className={cn(
            "w-full justify-between font-normal",
            !value && "text-muted-foreground",
            className
          )}
          disabled={disabled}
        >
          {value ? value.toLocaleDateString() : placeholder}
          <ChevronDownIcon className="h-4 w-4" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto overflow-hidden p-0" align="start">
        <Calendar
          mode="single"
          selected={value}
          captionLayout="dropdown"
          onSelect={handleDateSelect}
          disabled={(date) => date < new Date(new Date().setHours(0, 0, 0, 0))}
        />
      </PopoverContent>
    </Popover>
  );
}
