import { useState } from 'react'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { List, Card } from '@/types'
import { CardItem } from '@/components/CardItem'
import { CreateCardModal } from '@/components/CreateCardModal'
import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { listsApi } from '@/services/lists'

interface ListColumnProps {
  list: List
  onCardClick: (card: Card) => void
}

export const ListColumn: React.FC<ListColumnProps> = ({ list, onCardClick }) => {
  const [isCreateCardModalOpen, setIsCreateCardModalOpen] = useState(false)
  const queryClient = useQueryClient()

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: list.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  const deleteListMutation = useMutation({
    mutationFn: listsApi.deleteList,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['boards'] })
    },
  })

  const handleDeleteList = () => {
    if (confirm('Are you sure you want to delete this list? All cards will be deleted.')) {
      deleteListMutation.mutate(list.id)
    }
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className="w-72 bg-gray-100 rounded-lg p-4 flex-shrink-0"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-900">{list.title}</h3>
        <button
          onClick={handleDeleteList}
          className="text-gray-400 hover:text-red-600"
        >
          <TrashIcon className="w-4 h-4" />
        </button>
      </div>

      <SortableContext
        items={list.cards.map((card) => card.id)}
        strategy={verticalListSortingStrategy}
      >
        <div className="space-y-3 mb-4">
          {list.cards.map((card) => (
            <CardItem
              key={card.id}
              card={card}
              onClick={() => onCardClick(card)}
            />
          ))}
        </div>
      </SortableContext>

      <button
        onClick={() => setIsCreateCardModalOpen(true)}
        className="w-full flex items-center justify-center space-x-2 py-2 text-gray-500 hover:text-gray-700 border-2 border-dashed border-gray-300 rounded-lg hover:border-gray-400 transition-colors"
      >
        <PlusIcon className="w-5 h-5" />
        <span>Add a card</span>
      </button>

      <CreateCardModal
        isOpen={isCreateCardModalOpen}
        onClose={() => setIsCreateCardModalOpen(false)}
        onSubmit={(data) => {
          // Handle card creation
          setIsCreateCardModalOpen(false)
        }}
        isLoading={false}
        listId={list.id}
      />
    </div>
  )
}

