import { useState, useEffect } from 'react'
import { ArrowUpRight } from 'lucide-react'

interface Props {
  timestamp: string | null
}

export const LastUpdateIndicator = ({ timestamp }: Props) => {
  const [pulse, setPulse] = useState(false)

  useEffect(() => {
    if (timestamp) {
      setPulse(true)
      const t = setTimeout(() => setPulse(false), 1000)
      return () => clearTimeout(t)
    }
  }, [timestamp])

  if (!timestamp) return null

  const time = new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

  return (
    <div className="flex items-center gap-1 text-xs text-muted-foreground">
      <ArrowUpRight 
        className={`w-3 h-3 transition-transform ${pulse ? 'scale-150 text-green-500' : ''}`}
      />
      <span>Updated {time}</span>
    </div>
  )
}
