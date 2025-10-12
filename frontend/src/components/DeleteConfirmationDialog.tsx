import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Archive, AlertTriangle } from "lucide-react";

interface ArchiveConfirmationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
  itemName: string;
  isLoading?: boolean;
}

export default function ArchiveConfirmationDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  description,
  itemName,
  isLoading = false,
}: ArchiveConfirmationDialogProps) {
  const [confirmationText, setConfirmationText] = useState("");
  const [isValid, setIsValid] = useState(false);

  // Reset confirmation text when dialog opens/closes
  useEffect(() => {
    if (isOpen) {
      setConfirmationText("");
      setIsValid(false);
    }
  }, [isOpen]);

  // Check if the confirmation text matches the item name
  useEffect(() => {
    setIsValid(confirmationText === itemName);
  }, [confirmationText, itemName]);

  const handleClose = () => {
    setConfirmationText("");
    setIsValid(false);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[425px] p-4">
        <DialogHeader className="pb-3">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-red-100">
              <AlertTriangle className="h-4 w-4 text-red-600" />
            </div>
            <div>
              <DialogTitle className="text-left text-base">{title}</DialogTitle>
              <DialogDescription className="text-left text-xs">
                {description}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="py-2">
          <div className="rounded-md bg-orange-50 p-3">
            <div className="flex gap-2">
              <Archive className="h-4 w-4 text-orange-400 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-sm font-medium text-orange-800">
                  Are you sure you want to archive "{itemName}"?
                </h3>
                <p className="mt-1 text-xs text-orange-700">
                  This will archive the project and hide it from the main view.
                  You can restore it later if needed.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div>
          <div className="space-y-6">
            <label
              htmlFor="confirmation-input"
              className="text-sm font-medium text-gray-700"
            >
              To confirm, type{" "}
              <span className="font-mono bg-gray-100 px-1 rounded text-xs">
                {itemName}
              </span>{" "}
              below:
            </label>
            <Input
              id="confirmation-input"
              type="text"
              value={confirmationText}
              onChange={(e) => setConfirmationText(e.target.value)}
              placeholder={`Type "${itemName}" to confirm`}
              className="w-full h-9 mt-1"
              autoFocus
            />
          </div>
        </div>

        <DialogFooter className="pt-3">
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={isLoading}
            className="h-8 px-3 text-sm"
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            onClick={onConfirm}
            disabled={isLoading || !isValid}
            className="bg-orange-600 hover:bg-orange-700 disabled:opacity-50 h-8 px-3 text-sm"
          >
            {isLoading ? (
              <>
                <div className="mr-1.5 h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Archiving...
              </>
            ) : (
              <>
                <Archive className="mr-1.5 h-3 w-3" />
                Archive
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
