// tasker/frontend/src/components/CardItem.tsx
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Card } from '@/types'
import { format } from 'date-fns'
import { CardAssignment } from './CardAssignment'
import { EyeIcon } from '@heroicons/react/24/outline'
import { useState } from 'react'

interface CardItemProps {
  card: Card
  boardId: string
  onOpenModal: () => void
  onCardUpdate?: (card: Card) => void
}

export const CardItem: React.FC<CardItemProps> = ({ card, boardId, onOpenModal, onCardUpdate }) => {
  const [isHoveringInteractive, setIsHoveringInteractive] = useState(false)

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: card.id,
    disabled: isHoveringInteractive,
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  const isOverdue = card.due_date && new Date(card.due_date) < new Date()

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="bg-white rounded-lg p-3 shadow-sm border border-gray-200 cursor-grab active:cursor-grabbing hover:shadow-md transition-shadow"
      {...(isHoveringInteractive ? {} : { ...attributes, ...listeners })}
    >
      <div className="flex justify-between items-start mb-2">
        <h4 className="font-medium text-gray-900 flex-1 pr-2">{card.title}</h4>

        {/* Read More Button */}
        <div
          onMouseEnter={() => setIsHoveringInteractive(true)}
          onMouseLeave={() => setIsHoveringInteractive(false)}
          className="pointer-events-auto"
        >
          <button
            onClick={(e) => {
              e.stopPropagation()
              onOpenModal()  // Opens CardModal
            }}
            className="text-gray-400 hover:text-gray-600 p-1 rounded hover:bg-gray-100"
            title="View details"
          >
            <EyeIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      {card.description && (
        <p className="text-sm text-gray-600 mb-2 line-clamp-2">
          {card.description}
        </p>
      )}

      <div className="flex items-center justify-between text-xs text-gray-500">
        <div
          onMouseEnter={() => setIsHoveringInteractive(true)}
          onMouseLeave={() => setIsHoveringInteractive(false)}
          className="pointer-events-auto"
        >
          <CardAssignment 
            card={card} 
            boardId={boardId} 
            onAssignmentChange={onCardUpdate}
          />
        </div>

        {card.due_date && (
          <span className={`${isOverdue ? 'text-red-600' : 'text-gray-500'}`}>
            {format(new Date(card.due_date), 'MMM d')}
          </span>
        )}
      </div>
    </div>
  )
}