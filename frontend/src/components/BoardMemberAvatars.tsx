import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { boardsApi, BoardMember } from '@/services/boards'

interface BoardMemberAvatarsProps {
  boardId: string
  maxVisible?: number
  size?: 'sm' | 'md' | 'lg'
  showTooltip?: boolean
}

export const BoardMemberAvatars: React.FC<BoardMemberAvatarsProps> = ({
  boardId,
  maxVisible = 3,
  size = 'md',
  showTooltip = true
}) => {
  const { data: membersData, isLoading } = useQuery({
    queryKey: ['board-members', boardId],
    queryFn: () => boardsApi.getBoardMembers(boardId),
    enabled: !!boardId,
  })

  if (isLoading) {
    return (
      <div className="flex items-center space-x-1">
        <div className="animate-pulse bg-gray-200 rounded-full h-6 w-6"></div>
        <div className="animate-pulse bg-gray-200 rounded-full h-6 w-6"></div>
        <div className="animate-pulse bg-gray-200 rounded-full h-6 w-6"></div>
      </div>
    )
  }

  const members: BoardMember[] = membersData?.members || []
  const visibleMembers = members.slice(0, maxVisible)
  const remainingCount = Math.max(0, members.length - maxVisible)

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'h-6 w-6 text-xs'
      case 'lg':
        return 'h-10 w-10 text-sm'
      default:
        return 'h-8 w-8 text-sm'
    }
  }

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(word => word.charAt(0))
      .join('')
      .toUpperCase()
      .slice(0, 2)
  }

  const getAvatarColor = (name: string) => {
    const colors = [
      'bg-blue-500',
      'bg-green-500',
      'bg-purple-500',
      'bg-pink-500',
      'bg-indigo-500',
      'bg-yellow-500',
      'bg-red-500',
      'bg-teal-500',
    ]
    const index = name.charCodeAt(0) % colors.length
    return colors[index]
  }

  return (
    <div className="flex items-center space-x-1">
      {visibleMembers.map((member) => (
        <div
          key={member.id}
          className={`relative group ${getSizeClasses()}`}
        >
          <div
            className={`${getSizeClasses()} ${getAvatarColor(member.full_name)} text-white rounded-full flex items-center justify-center font-medium border-2 border-white shadow-sm`}
          >
            {getInitials(member.full_name)}
          </div>
          {showTooltip && (
            <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap z-10">
              <div className="font-medium">{member.full_name}</div>
              <div className="text-gray-300">{member.email}</div>
              <div className="text-gray-400 capitalize">{member.role}</div>
              <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
            </div>
          )}
        </div>
      ))}
      {remainingCount > 0 && (
        <div className={`${getSizeClasses()} bg-gray-300 text-gray-600 rounded-full flex items-center justify-center font-medium border-2 border-white shadow-sm`}>
          +{remainingCount}
        </div>
      )}
    </div>
  )
}
