// tasker/frontend/src/components/CardAssignment.tsx
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib-custom/api';
import { Card } from '@/types';
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
}

export function CardAssignment({ card, boardId, onAssignmentChange }: CardAssignmentProps) {
  const [isOpen, setIsOpen] = useState(false);
  const queryClient = useQueryClient();

  const { data: membersData, isLoading: membersLoading } = useQuery({
    queryKey: ['board-members', boardId],
    queryFn: async () => (await api.get(`/boards/${boardId}/members`)).data,
    enabled: !!boardId,
    staleTime: 5 * 60 * 1000,
  });

  const assignMutation = useMutation({
    mutationFn: (userId: string) => api.patch(`/cards/${card.id}/assign/${userId}`),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['board', boardId] });
      onAssignmentChange?.(data);
      setIsOpen(false);
    },
  });

  const unassignMutation = useMutation({
    mutationFn: () => api.patch(`/cards/${card.id}/unassign`),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['board', boardId] });
      onAssignmentChange?.(data);
      setIsOpen(false);
    },
  });

  const members: BoardMember[] = membersData?.members || [];

  const toggleOpen = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsOpen(prev => !prev);
  };

  const handleAssign = (e: React.MouseEvent, userId: string) => {
    e.stopPropagation();
    assignMutation.mutate(userId);
  };

  const handleUnassign = (e: React.MouseEvent) => {
    e.stopPropagation();
    unassignMutation.mutate();
  };

  return (
    <div className="relative inline-block">
      <button
        onClick={toggleOpen}
        className="flex items-center space-x-1 text-xs text-gray-600 hover:text-gray-800 bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded-md transition-colors disabled:opacity-50 pointer-events-auto"
        disabled={assignMutation.isPending || unassignMutation.isPending}
      >
        <UserIcon className="w-3.5 h-3.5" />
        <span>
          {assignMutation.isPending || unassignMutation.isPending
            ? 'Saving...'
            : card.assignee?.full_name || 'Assign'}
        </span>
      </button>

      {isOpen && (
        <>
          <div className="absolute top-full left-0 mt-1 w-56 bg-white border border-gray-200 rounded-md shadow-lg z-50 p-2">
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-xs font-medium">Assign to</h3>
              <button onClick={(e) => { e.stopPropagation(); setIsOpen(false); }}>
                <XMarkIcon className="w-3.5 h-3.5 text-gray-400 hover:text-gray-600" />
              </button>
            </div>

            {card.assignee && (
              <button
                onClick={handleUnassign}
                className="w-full text-left px-2 py-1.5 text-xs text-red-600 hover:bg-red-50 rounded flex items-center space-x-1"
                disabled={unassignMutation.isPending}
              >
                <XMarkIcon className="w-3.5 h-3.5" />
                <span>Unassign</span>
              </button>
            )}

            {membersLoading ? (
              <div className="px-2 py-1.5 text-xs text-gray-500">Loading...</div>
            ) : members.length === 0 ? (
              <div className="px-2 py-1.5 text-xs text-gray-500">No members</div>
            ) : (
              <div className="max-h-40 overflow-y-auto">
                {members.map(member => (
                  <button
                    key={member.id}
                    onClick={(e) => handleAssign(e, member.id)}
                    className={`w-full text-left px-2 py-1.5 text-xs rounded flex items-center space-x-2 transition-colors pointer-events-auto ${
                      card.assignee_id === member.id
                        ? 'bg-blue-100 text-blue-900 font-medium'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                    disabled={assignMutation.isPending || card.assignee_id === member.id}
                  >
                    <div className="w-5 h-5 bg-gray-400 rounded-full flex items-center justify-center text-xs font-medium text-white">
                      {member.full_name[0].toUpperCase()}
                    </div>
                    <div className="flex-1 text-left min-w-0">
                      <div className="truncate text-xs font-medium">{member.full_name}</div>
                      <div className="truncate text-xs text-gray-500">{member.email}</div>
                    </div>
                    {member.role === 'owner' && (
                      <span className="text-xs bg-yellow-100 text-yellow-800 px-1.5 py-0.5 rounded text-xs">Owner</span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div
            className="fixed inset-0 z-40 bg-transparent"
            onClick={(e) => { e.stopPropagation(); setIsOpen(false); }}
          />
        </>
      )}
    </div>
  );
}