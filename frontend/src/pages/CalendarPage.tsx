import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import { boardsApi } from '@/services/boards'

export const CalendarPage: React.FC = () => {
  const { boardId } = useParams<{ boardId: string }>()

  const { data: board } = useQuery({
    queryKey: ['board', boardId],
    queryFn: () => boardsApi.getBoard(boardId!),
    enabled: !!boardId,
  })

  const events =
    board?.lists?.flatMap((list) =>
      list.cards
        .filter((card) => card.due_date)
        .map((card) => ({
          title: card.title,
          date: card.due_date,
        }))
    ) || []

  return (
    <div className="bg-white rounded-xl shadow-md p-4">
      <FullCalendar
        plugins={[dayGridPlugin]}
        initialView="dayGridMonth"
        events={events}
        height="75vh"
      />
    </div>
  )
}
