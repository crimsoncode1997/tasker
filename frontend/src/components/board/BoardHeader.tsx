import { useBoard } from '@/hooks/useBoard'
import { LastUpdateIndicator } from '@/components/ui/LastUpdateIndicator'

export const BoardHeader = () => {
  const { board } = useBoard()

  if (!board) return null

  return (
    <div className="flex items-center justify-between p-4 border-b bg-background">
      <h1 className="text-2xl font-bold">{board.title}</h1>
      <LastUpdateIndicator timestamp={board.updated_at} />
    </div>
  )
}
