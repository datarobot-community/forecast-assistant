import React, { useState, useRef } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faFolder } from "@fortawesome/free-solid-svg-icons/faFolder";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "~/components/ui/dialog";
import { Button } from "~/components/ui/button";
import { Input } from "~/components/ui/input";
import { Textarea } from "~/components/ui/textarea";

export type Customizations = {
  featureName: string;
  date: string;
  value: number;
};

type Props = {
  onConfirm: (customizations: Customizations[]) => void;
  onDismiss: () => void;
};

const BulkScenarioEditorModal = ({ onConfirm, onDismiss }: Props) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [content, setContent] = useState("");

  const onFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event?.target?.files?.[0];
    if (!file) return;

    try {
      const reader = new FileReader();
      reader.onload = (e: ProgressEvent<FileReader>) => {
        const fileContent = e?.target?.result as string;
        // Removing the headers line
        const lines = fileContent.trim().split("\n");
        lines.shift();

        setContent(lines.join("\n"));
      };
      reader.readAsText(file);
    } catch (error) {
      console.log(error);
    } finally {
      event.target.value = "";
    }
  };

  const handleConfirm = () => {
    const lines = content.trim().split("\n");
    const customizations = lines.map((line) => {
      let [featureName, date, value] = line.split(",");

      // Remove spaces
      featureName = featureName.trim();
      date = date.trim();
      value = value.trim();

      return { featureName, date, value: Number(value) };
    });

    onConfirm(customizations);
  };

  return (
    <Dialog
      open
      onOpenChange={(isOpen) => {
        if (!isOpen) {
          onDismiss();
        }
      }}
    >
      <DialogContent className='sm:max-w-[480px]'>
        <DialogHeader>
          <DialogTitle>Bulk Scenario Editor</DialogTitle>
          <DialogDescription>
            Quickly create complex scenarios by uploading or pasting a CSV with
            the desired customizations.
          </DialogDescription>
        </DialogHeader>
        <div className='flex flex-col gap-4'>
          <div
            className='flex items-center justify-center gap-2 p-4 border border-dashed rounded-md cursor-pointer'
            onClick={() => {
              inputRef.current?.click();
            }}
          >
            <span>Drop a file here to upload or</span>
            <Button variant='ghost'>
              <FontAwesomeIcon icon={faFolder} className='mr-2' />
              Browse files
            </Button>
            <Input
              className='hidden'
              type='file'
              accept='.csv'
              ref={inputRef}
              onChange={onFileUpload}
            />
          </div>
          <Textarea
            rows={8}
            placeholder='Example customization:&#10;Sales, April-10-2024, 1000'
            value={content}
            onChange={(e) => setContent(e.target.value)}
          />
        </div>
        <DialogFooter>
          <Button variant='outline' onClick={onDismiss}>
            Cancel
          </Button>
          <Button onClick={handleConfirm}>Add customizations</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default BulkScenarioEditorModal;
