import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { PlusIcon } from '@heroicons/react/24/outline'
import { boardsApi } from '@/services/boards'
import { CreateBoardModal } from '@/components/CreateBoardModal'
import { useNotifications } from '@/contexts/NotificationContext'

export const DashboardPage: React.FC = () => {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const queryClient = useQueryClient()
  const { refreshNotifications } = useNotifications()

  const { data: boards = [], isLoading } = useQuery({
    queryKey: ['boards'],
    queryFn: boardsApi.getBoards,
  })

  // Refresh boards when notifications are updated (in case of new invitations)
  useEffect(() => {
    refreshNotifications()
    queryClient.invalidateQueries({ queryKey: ['boards'] })
  }, [refreshNotifications, queryClient])

  const createBoardMutation = useMutation({
    mutationFn: boardsApi.createBoard,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['boards'] })
      setIsCreateModalOpen(false)
    },
  })

  const deleteBoardMutation = useMutation({
    mutationFn: boardsApi.deleteBoard,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['boards'] })
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Your Boards</h1>
          <p className="text-gray-600">Manage your projects and tasks</p>
        </div>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="btn btn-primary flex items-center space-x-2"
        >
          <PlusIcon className="w-5 h-5" />
          <span>Create Board</span>
        </button>
      </div>

      {boards.length === 0 ? (
        <div className="text-center py-12">
          <div className="mx-auto h-24 w-24 bg-gray-100 rounded-full flex items-center justify-center mb-4">
            <PlusIcon className="w-12 h-12 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No boards yet</h3>
          <p className="text-gray-600 mb-6">Create your first board to get started</p>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="btn btn-primary"
          >
            Create Board
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {boards.map((board) => (
            <div key={board.id} className="card p-6 hover:shadow-md transition-shadow">
              <Link to={`/board/${board.id}`} className="block">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {board.title}
                </h3>
                {board.description && (
                  <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                    {board.description}
                  </p>
                )}
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <span>{board.lists.length} lists</span>
                  <span>
                    {new Date(board.updated_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="mt-2">
                  {board.user_role === 'owner' ? (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      Owner
                    </span>
                  ) : board.user_role ? (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      {board.user_role === 'admin' ? 'Admin' : 'Member'} of {board.owner.full_name}'s board
                    </span>
                  ) : null}
                </div>
              </Link>
              
              {board.user_role === 'owner' && (
                <div className="mt-4 flex justify-end">
                  <button
                    onClick={(e) => {
                      e.preventDefault()
                      if (confirm('Are you sure you want to delete this board?')) {
                        deleteBoardMutation.mutate(board.id)
                      }
                    }}
                    className="text-red-600 hover:text-red-700 text-sm"
                  >
                    Delete
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <CreateBoardModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={createBoardMutation.mutate}
        isLoading={createBoardMutation.isPending}
      />
    </div>
  )
}

