"use client";

import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";

/**
 * Confirms leaving a lesson in progress.
 *
 * Worth interrupting for: quitting forfeits the XP and the crown, and the
 * hearts already spent are not returned.
 */
interface QuitModalProps {
  onCancel: () => void;
  onConfirm: () => void;
}

export function QuitModal({ onCancel, onConfirm }: QuitModalProps) {
  return (
    <Modal title="Wait, don't go!" onClose={onCancel} accentColor="#FF9600" icon="flame">
      <p className="mb-6 text-center text-sm font-bold text-wolf">
        You&apos;re almost there. Quitting now loses the progress in this lesson.
      </p>
      <div className="flex flex-col gap-3">
        <Button variant="primary" size="lg" fullWidth onClick={onCancel}>
          Keep learning
        </Button>
        <Button variant="ghost" size="lg" fullWidth onClick={onConfirm}>
          End session
        </Button>
      </div>
    </Modal>
  );
}
