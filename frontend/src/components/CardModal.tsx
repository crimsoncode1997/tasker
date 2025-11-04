// tasker/frontend/src/components/CardModal.tsx
import { useState } from "react";
import { Dialog } from "@headlessui/react";
import { XMarkIcon, PencilIcon, TrashIcon } from "@heroicons/react/24/outline";
import { Card } from "@/types";
import { format } from "date-fns";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { cardsApi } from "@/services/cards";

interface CardModalProps {
  card: Card;
  isOpen: boolean; // ← ADDED
  onClose: () => void;
}

export const CardModal: React.FC<CardModalProps> = ({
  card,
  isOpen,
  onClose,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState(card.title);
  const [description, setDescription] = useState(card.description || "");
  const [dueDate, setDueDate] = useState(card.due_date || "");

  const queryClient = useQueryClient();

  const updateCardMutation = useMutation({
    mutationFn: (data: Partial<Card>) => cardsApi.updateCard(card.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["board", card.board_id] });
      queryClient.invalidateQueries({ queryKey: ["boards"] });
      setIsEditing(false);
    },
  });

  const deleteCardMutation = useMutation({
    mutationFn: () => cardsApi.deleteCard(card.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["board", card.board_id] });
      queryClient.invalidateQueries({ queryKey: ["boards"] });
      onClose();
    },
  });

  const handleSave = () => {
    updateCardMutation.mutate({
      title,
      description,
      due_date: dueDate || undefined,
    });
  };

  const handleDelete = () => {
    if (confirm("Are you sure you want to delete this card?")) {
      deleteCardMutation.mutate();
    }
  };

  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/25" aria-hidden="true" />

      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="mx-auto max-w-2xl rounded bg-white p-6 w-full">
          <div className="flex items-center justify-between mb-4">
            <Dialog.Title className="text-lg font-medium text-gray-900">
              Card Details
            </Dialog.Title>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setIsEditing(!isEditing)}
                className="text-gray-400 hover:text-gray-600"
              >
                <PencilIcon className="w-5 h-5" />
              </button>
              <button
                onClick={handleDelete}
                className="text-gray-400 hover:text-red-600"
              >
                <TrashIcon className="w-5 h-5" />
              </button>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Title
              </label>
              {isEditing ? (
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="input"
                />
              ) : (
                <p className="text-lg font-semibold text-gray-900">{title}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              {isEditing ? (
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={4}
                  className="input"
                />
              ) : (
                <p className="text-gray-700 whitespace-pre-wrap">
                  {description || "No description"}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Due Date
              </label>
              {isEditing ? (
                <input
                  type="date"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="input"
                />
              ) : (
                <p className="text-gray-700">
                  {card.due_date
                    ? format(new Date(card.due_date), "PPP")
                    : "No due date"}
                </p>
              )}
            </div>

            {card.assignee && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Assignee
                </label>
                <div className="flex items-center space-x-2">
                  <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                    <span className="text-primary-600 font-medium">
                      {card.assignee.full_name.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <span className="text-gray-700">
                    {card.assignee.full_name}
                  </span>
                </div>
              </div>
            )}

            <div className="flex items-center justify-between text-sm text-gray-500">
              <span>Created {format(new Date(card.created_at), "PPP")}</span>
              <span>Updated {format(new Date(card.updated_at), "PPP")}</span>
            </div>
          </div>

          {isEditing && (
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setIsEditing(false)}
                className="btn btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={updateCardMutation.isPending}
                className="btn btn-primary"
              >
                {updateCardMutation.isPending ? "Saving..." : "Save Changes"}
              </button>
            </div>
          )}
        </Dialog.Panel>
      </div>
    </Dialog>
  );
};
