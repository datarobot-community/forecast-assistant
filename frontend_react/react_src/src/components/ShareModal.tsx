import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "~/components/ui/dialog";
import { Button } from "~/components/ui/button";
import { Label } from "~/components/ui/label";
import { Input } from "~/components/ui/input";
import shareApplication from "~/api/shareApplication";
import { useToast } from "~/hooks/use-toast";

type Props = {
  onDismiss: () => void;
};

const ShareModal = ({ onDismiss }: Props) => {
  const [email, setEmail] = useState("");
  const [isSharing, setIsSharing] = useState(false);
  const { toast } = useToast();

  const handleConfirm = async () => {
    if (email === "") {
      return;
    }

    try {
      setIsSharing(true);
      await shareApplication([email]);
      setIsSharing(false);
      setEmail("");
      toast({
        title: "Application shared successfully",
      });
    } catch (error) {
      console.error(error);
      toast({
        title: "Failed to share application",
      });
    } finally {
      setIsSharing(false);
    }
  };

  const enableShareButton = email !== "" && !isSharing;

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
          <DialogTitle>Share with others</DialogTitle>
          <DialogDescription>
            Enter the email addresses or usernames of the people you want to
            share this application with.
          </DialogDescription>
        </DialogHeader>
        <div className='flex flex-col gap-1.5'>
          <Label htmlFor='email'>Share with</Label>
          <Input
            id='email'
            placeholder='joe.doe@datarobot.com'
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <DialogFooter>
          <Button variant='outline' onClick={onDismiss}>
            Cancel
          </Button>
          <Button onClick={handleConfirm} disabled={!enableShareButton}>
            Share
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ShareModal;
