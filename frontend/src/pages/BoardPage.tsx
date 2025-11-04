import { useParams, Link, Outlet, Routes, Route } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { boardsApi } from '@/services/boards'
import { listsApi } from '@/services/lists'
import { BoardView } from '@/components/BoardView'
import { CreateListModal } from '@/components/CreateListModal'
import { CollaborationStatus } from '@/components/CollaborationStatus'
import { BoardMemberAvatars } from '@/components/BoardMemberAvatars'
import { BoardCollaborationProvider } from '@/contexts/BoardCollaborationContext'
import { useBoardInvitations, InviteUserModal } from '@/hooks/useBoardInvitations'
import { useState } from 'react'
import { PlusIcon, UserPlusIcon } from '@heroicons/react/24/outline'
import { CalendarPage } from './CalendarPage'

export const BoardPage: React.FC = () => {
  const { boardId } = useParams<{ boardId: string }>()
  const [isCreateListModalOpen, setIsCreateListModalOpen] = useState(false)
  const queryClient = useQueryClient()

  const {
    inviteEmail,
    setInviteEmail,
    inviteRole,
    setInviteRole,
    isInviteModalOpen,
    openInviteModal,
    closeInviteModal,
    inviteUser,
    isInviting,
    inviteError
  } = useBoardInvitations(boardId!)

  const { data: board, isLoading } = useQuery({
    queryKey: ['board', boardId],
    queryFn: () => boardsApi.getBoard(boardId!),
    enabled: !!boardId,
  })

  const createListMutation = useMutation({
    mutationFn: listsApi.createList,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['board', boardId] })
      setIsCreateListModalOpen(false)
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!board) {
    return <div className="text-center py-12"><h2>Board not found</h2></div>
  }

  return (
    <BoardCollaborationProvider boardId={boardId!}>
      <div>
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{board.title}</h1>
            {board.description && <p className="text-gray-600">{board.description}</p>}
            <CollaborationStatus className="mt-2" />
          </div>

          <div className="flex space-x-2">
            <button onClick={openInviteModal} className="btn btn-secondary flex items-center space-x-2">
              <UserPlusIcon className="w-5 h-5" />
              <span>Invite</span>
            </button>
            <button onClick={() => setIsCreateListModalOpen(true)} className="btn btn-primary flex items-center space-x-2">
              <PlusIcon className="w-5 h-5" />
              <span>Add List</span>
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-6 mb-6 border-b pb-2">
          <Link to={`/board/${boardId}`} className="text-blue-600 hover:underline">
            Board
          </Link>
          <Link to={`/board/${boardId}/calendar`} className="text-blue-600 hover:underline">
            Calendar
          </Link>
        </div>

        {/* Routes for board view and calendar */}
        <Routes>
          <Route path="/" element={<BoardView boardId={boardId!} />} />
          <Route path="calendar" element={<CalendarPage />} />
        </Routes>

        <CreateListModal
          isOpen={isCreateListModalOpen}
          onClose={() => setIsCreateListModalOpen(false)}
          onSubmit={(data) => createListMutation.mutate({ ...data, board_id: boardId! })}
          isLoading={createListMutation.isPending}
        />

        <InviteUserModal
          isOpen={isInviteModalOpen}
          onClose={closeInviteModal}
          onInvite={inviteUser}
          isInviting={isInviting}
          error={inviteError}
        />
      </div>
    </BoardCollaborationProvider>
  )
}
