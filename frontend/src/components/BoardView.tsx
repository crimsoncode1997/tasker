import { useState } from 'react'
import { DndContext, DragEndEvent, DragStartEvent } from '@dnd-kit/core'
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
    onMutate: async (variables) => {
      await queryClient.cancelQueries({ queryKey: ['board', board.id] })
      const previous = queryClient.getQueryData<Board>(['board', board.id])
      if (previous) {
        const updated: Board = {
          ...previous,
          lists: previous.lists.map((l) => ({ ...l, cards: [...l.cards] })),
        }
        // Remove card from its current list
        const sourceList = updated.lists.find((l) => l.cards.some((c) => c.id === variables.card_id))
        const destList = updated.lists.find((l) => l.id === variables.list_id)
        if (sourceList && destList) {
          const cardIndex = sourceList.cards.findIndex((c) => c.id === variables.card_id)
          if (cardIndex !== -1) {
            const [moved] = sourceList.cards.splice(cardIndex, 1)
            moved.list_id = destList.id
            const insertIndex = Math.min(Math.max(variables.position, 0), destList.cards.length)
            destList.cards.splice(insertIndex, 0, moved)
            // Renumber positions locally
            destList.cards.forEach((c, idx) => (c.position = idx))
            sourceList.cards.forEach((c, idx) => (c.position = idx))
          }
        }
        queryClient.setQueryData(['board', board.id], updated)
      }
      return { previous }
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(['board', board.id], context.previous)
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['board', board.id] })
    },
  })

  const reorderCardsMutation = useMutation({
    mutationFn: ({ listId, positions }: { listId: string; positions: any[] }) =>
      cardsApi.reorderCards(listId, positions),
    onMutate: async ({ listId, positions }) => {
      await queryClient.cancelQueries({ queryKey: ['board', board.id] })
      const previous = queryClient.getQueryData<Board>(['board', board.id])
      if (previous) {
        const updated: Board = {
          ...previous,
          lists: previous.lists.map((l) => ({ ...l, cards: [...l.cards] })),
        }
        const targetList = updated.lists.find((l) => l.id === listId)
        if (targetList) {
          // Apply new order based on provided positions
          const idToCard = new Map(targetList.cards.map((c) => [c.id, c]))
          targetList.cards = positions
            .slice()
            .sort((a, b) => a.position - b.position)
            .map((p) => {
              const card = idToCard.get(p.card_id)!
              card.position = p.position
              return card
            })
        }
        queryClient.setQueryData(['board', board.id], updated)
      }
      return { previous }
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(['board', board.id], context.previous)
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['board', board.id] })
    },
  })

  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event
    const card = findCard(active.id as string)
    setActiveCard(card)
  }

  const handleCardUpdate = (updatedCard: Card) => {
    // Update the card in the board data
    queryClient.setQueryData<Board>(['board', board.id], (oldBoard) => {
      if (!oldBoard) return oldBoard;
      
      return {
        ...oldBoard,
        lists: oldBoard.lists.map(list => ({
          ...list,
          cards: list.cards.map(card => 
            card.id === updatedCard.id ? updatedCard : card
          )
        }))
      };
    });
  };

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
    // Reordering within the same list
    else if (overCard && card.list_id === overCard.list_id) {
      const targetList = findList(card.list_id)
      if (!targetList) return

      const cards = [...targetList.cards]
      const fromIndex = cards.findIndex((c) => c.id === card.id)
      const toIndex = cards.findIndex((c) => c.id === overCard.id)
      if (fromIndex === -1 || toIndex === -1 || fromIndex === toIndex) return

      const [moved] = cards.splice(fromIndex, 1)
      cards.splice(toIndex, 0, moved)

      const positions = cards.map((c, idx) => ({ card_id: c.id, position: idx }))
      reorderCardsMutation.mutate({ listId: targetList.id, positions })
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
                boardId={board.id}
                onCardClick={setSelectedCard}
                onCardUpdate={handleCardUpdate}
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

