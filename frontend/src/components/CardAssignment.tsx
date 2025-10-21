/**
 * Card assignment component for assigning users to cards.
 */
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib-custom/api';
import { Card, User } from '@/types';
import { UserIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface CardAssignmentProps {
  card: Card;
  boardId: string;
  onAssignmentChange?: (card: Card) => void;
}

interface BoardMember {
  id: string;
  email: string;
  full_name: string;
  role: string;
  joined_at: string;
}

export function CardAssignment({ card, boardId, onAssignmentChange }: CardAssignmentProps) {
  const [isOpen, setIsOpen] = useState(false);
  const queryClient = useQueryClient();

  // Fetch board members
  const { data: membersData, isLoading: membersLoading } = useQuery({
    queryKey: ['board-members', boardId],
    queryFn: async () => {
      const response = await api.get(`/boards/${boardId}/members`);
      return response.data;
    },
    enabled: isOpen
  });

  // Assign card mutation
  const assignMutation = useMutation({
    mutationFn: async (userId: string) => {
      const response = await api.patch(`/cards/${card.id}/assign/${userId}`);
      return response.data;
    },
    onSuccess: (updatedCard) => {
      queryClient.invalidateQueries({ queryKey: ['board', boardId] });
      onAssignmentChange?.(updatedCard);
      setIsOpen(false);
    },
    onError: (error) => {
      console.error('Failed to assign card:', error);
    }
  });

  // Unassign card mutation
  const unassignMutation = useMutation({
    mutationFn: async () => {
      const response = await api.patch(`/cards/${card.id}/unassign`);
      return response.data;
    },
    onSuccess: (updatedCard) => {
      queryClient.invalidateQueries({ queryKey: ['board', boardId] });
      onAssignmentChange?.(updatedCard);
    },
    onError: (error) => {
      console.error('Failed to unassign card:', error);
    }
  });

  const handleAssign = (userId: string) => {
    assignMutation.mutate(userId);
  };

  const handleUnassign = () => {
    unassignMutation.mutate();
  };

  const members: BoardMember[] = membersData?.members || [];

  return (
    <div className="relative">
      {/* Assignment Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-1 text-sm text-gray-600 hover:text-gray-800 bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded-md transition-colors"
        disabled={assignMutation.isPending || unassignMutation.isPending}
      >
        <UserIcon className="w-4 h-4" />
        <span>
          {card.assignee ? card.assignee.full_name : 'Assign'}
        </span>
      </button>

      {/* Assignment Dropdown */}
      {isOpen && (
        <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-gray-200 rounded-md shadow-lg z-50">
          <div className="p-2">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-900">Assign to</h3>
              <button
                onClick={() => setIsOpen(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <XMarkIcon className="w-4 h-4" />
              </button>
            </div>

            {/* Unassign option */}
            {card.assignee && (
              <button
                onClick={handleUnassign}
                className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md flex items-center space-x-2"
                disabled={unassignMutation.isPending}
              >
                <XMarkIcon className="w-4 h-4" />
                <span>Unassign</span>
              </button>
            )}

            {/* Members list */}
            {membersLoading ? (
              <div className="px-3 py-2 text-sm text-gray-500">Loading members...</div>
            ) : (
              <div className="max-h-48 overflow-y-auto">
                {members.map((member) => (
                  <button
                    key={member.id}
                    onClick={() => handleAssign(member.id)}
                    className={`w-full text-left px-3 py-2 text-sm rounded-md flex items-center space-x-2 ${
                      card.assignee_id === member.id
                        ? 'bg-blue-100 text-blue-900'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                    disabled={assignMutation.isPending || card.assignee_id === member.id}
                  >
                    <div className="w-6 h-6 bg-gray-300 rounded-full flex items-center justify-center text-xs font-medium">
                      {member.full_name.charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1">
                      <div className="font-medium">{member.full_name}</div>
                      <div className="text-xs text-gray-500">{member.email}</div>
                    </div>
                    {member.role === 'owner' && (
                      <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                        Owner
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
}
