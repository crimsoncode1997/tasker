import { useState } from 'react'
import { DndContext, DragEndEvent, DragOverEvent, DragStartEvent } from '@dnd-kit/core'
import { SortableContext, horizontalListSortingStrategy } from '@dnd-kit/sortable'
import { ListColumn } from '@/components/ListColumn'
import { CardModal } from '@/components/CardModal'
import { Board, List, Card } from '@/types'
import { cardsApi } from '@/services/cards'
import { useMutation, useQueryClient } from '@tanstack/react-query'

interface BoardViewProps {
  board: Board
}

export const BoardView: React.FC<BoardViewProps> = ({ board }) => {
  const [activeCard, setActiveCard] = useState<Card | null>(null)
  const [selectedCard, setSelectedCard] = useState<Card | null>(null)
  const queryClient = useQueryClient()

  const moveCardMutation = useMutation({
    mutationFn: cardsApi.moveCard,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['board', board.id] })
    },
  })

  const reorderCardsMutation = useMutation({
    mutationFn: ({ listId, positions }: { listId: string; positions: any[] }) =>
      cardsApi.reorderCards(listId, positions),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['board', board.id] })
    },
  })

  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event
    const card = findCard(active.id as string)
    setActiveCard(card)
  }

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    setActiveCard(null)

    if (!over) return

    const card = findCard(active.id as string)
    const overList = findList(over.id as string)
    const overCard = findCard(over.id as string)

    if (!card) return

    // If dropping on a list
    if (overList && card.list_id !== overList.id) {
      const newPosition = overList.cards.length > 0 ? overList.cards.length : 0
      moveCardMutation.mutate({
        card_id: card.id,
        list_id: overList.id,
        position: newPosition,
      })
    }
    // If dropping on a card
    else if (overCard && card.list_id !== overCard.list_id) {
      const targetList = findList(overCard.list_id)
      if (targetList) {
        const newPosition = overCard.position
        moveCardMutation.mutate({
          card_id: card.id,
          list_id: targetList.id,
          position: newPosition,
        })
      }
    }
  }

  const findCard = (cardId: string): Card | null => {
    for (const list of board.lists) {
      const card = list.cards.find((c) => c.id === cardId)
      if (card) return card
    }
    return null
  }

  const findList = (listId: string): List | null => {
    return board.lists.find((l) => l.id === listId) || null
  }

  return (
    <div className="flex-1 overflow-x-auto pb-4">
      <DndContext
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <div className="flex space-x-4 min-w-max">
          <SortableContext
            items={board.lists.map((list) => list.id)}
            strategy={horizontalListSortingStrategy}
          >
            {board.lists.map((list) => (
              <ListColumn
                key={list.id}
                list={list}
                onCardClick={setSelectedCard}
              />
            ))}
          </SortableContext>
        </div>
      </DndContext>

      {selectedCard && (
        <CardModal
          card={selectedCard}
          onClose={() => setSelectedCard(null)}
        />
      )}
    </div>
  )
}

