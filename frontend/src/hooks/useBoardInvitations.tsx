/**
 * Hook for managing board invitations and member management.
 */
import React, { useState, useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib-custom/api';
import { Board } from '@/types';

interface InviteUserRequest {
  email: string;
  role?: 'member' | 'admin';
}

interface InviteUserResponse {
  success: boolean;
  message: string;
}

export function useBoardInvitations(boardId: string) {
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<'member' | 'admin'>('member');
  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);
  const queryClient = useQueryClient();

  const inviteUserMutation = useMutation<InviteUserResponse, Error, InviteUserRequest>({
    mutationFn: async (data: InviteUserRequest) => {
      const response = await api.post(`/boards/${boardId}/invite`, data);
      return response.data;
    },
    onSuccess: (data) => {
      // Invalidate board queries to refresh member list
      queryClient.invalidateQueries({ queryKey: ['board', boardId] });
      queryClient.invalidateQueries({ queryKey: ['boards'] });
      
      // Close modal and reset form
      setIsInviteModalOpen(false);
      setInviteEmail('');
      setInviteRole('member');
      
      // Show success message (you could add a toast notification here)
      console.log('User invited successfully:', data.message);
    },
    onError: (error) => {
      console.error('Failed to invite user:', error);
    }
  });

  const inviteUser = useCallback(async (email: string, role: 'member' | 'admin') => {
    if (!email.trim()) return;
    
    await inviteUserMutation.mutateAsync({
      email: email.trim(),
      role: role
    });
  }, [inviteUserMutation]);

  const openInviteModal = useCallback(() => {
    setIsInviteModalOpen(true);
  }, []);

  const closeInviteModal = useCallback(() => {
    setIsInviteModalOpen(false);
    setInviteEmail('');
    setInviteRole('member');
  }, []);

  return {
    inviteEmail,
    setInviteEmail,
    inviteRole,
    setInviteRole,
    isInviteModalOpen,
    openInviteModal,
    closeInviteModal,
    inviteUser,
    isInviting: inviteUserMutation.isPending,
    inviteError: inviteUserMutation.error?.message
  };
}

/**
 * Component for inviting users to a board.
 */
interface InviteUserModalProps {
  isOpen: boolean;
  onClose: () => void;
  onInvite: (email: string, role: 'member' | 'admin') => void;
  isInviting: boolean;
  error?: string;
}

export function InviteUserModal({ 
  isOpen, 
  onClose, 
  onInvite, 
  isInviting, 
  error 
}: InviteUserModalProps) {
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<'member' | 'admin'>('member');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (email.trim()) {
      onInvite(email.trim(), role);
      setEmail('');
      setRole('member');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-semibold mb-4">Invite User to Board</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email Address
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="user@example.com"
              required
            />
          </div>

          <div>
            <label htmlFor="role" className="block text-sm font-medium text-gray-700 mb-1">
              Role
            </label>
            <select
              id="role"
              value={role}
              onChange={(e) => setRole(e.target.value as 'member' | 'admin')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="member">Member</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          {error && (
            <div className="text-red-600 text-sm">
              {error}
            </div>
          )}

          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:text-gray-800"
              disabled={isInviting}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isInviting || !email.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isInviting ? 'Inviting...' : 'Send Invite'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
