import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Card } from '@/types'
import { format } from 'date-fns'

interface CardItemProps {
  card: Card
  onClick: () => void
}

export const CardItem: React.FC<CardItemProps> = ({ card, onClick }) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: card.id })

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
      {...attributes}
      {...listeners}
      onClick={onClick}
      className="bg-white rounded-lg p-3 shadow-sm border border-gray-200 cursor-pointer hover:shadow-md transition-shadow"
    >
      <h4 className="font-medium text-gray-900 mb-2">{card.title}</h4>
      
      {card.description && (
        <p className="text-sm text-gray-600 mb-2 line-clamp-2">
          {card.description}
        </p>
      )}

      <div className="flex items-center justify-between text-xs text-gray-500">
        {card.assignee && (
          <div className="flex items-center space-x-1">
            <div className="w-6 h-6 bg-primary-100 rounded-full flex items-center justify-center">
              <span className="text-primary-600 font-medium">
                {card.assignee.full_name.charAt(0).toUpperCase()}
              </span>
            </div>
            <span>{card.assignee.full_name}</span>
          </div>
        )}
        
        {card.due_date && (
          <span className={`${isOverdue ? 'text-red-600' : 'text-gray-500'}`}>
            {format(new Date(card.due_date), 'MMM d')}
          </span>
        )}
      </div>
    </div>
  )
}

