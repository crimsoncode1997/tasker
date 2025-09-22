import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Dialog } from '@headlessui/react'
import { XMarkIcon } from '@heroicons/react/24/outline'
import { cardsApi } from '@/services/cards'
import { useMutation, useQueryClient } from '@tanstack/react-query'

const createCardSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  description: z.string().optional(),
  due_date: z.string().optional(),
})

type CreateCardFormData = z.infer<typeof createCardSchema>

interface CreateCardModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: CreateCardFormData) => void
  isLoading: boolean
  listId: string
}

export const CreateCardModal: React.FC<CreateCardModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isLoading,
  listId,
}) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<CreateCardFormData>({
    resolver: zodResolver(createCardSchema),
  })

  const queryClient = useQueryClient()

  const createCardMutation = useMutation({
    mutationFn: (data: CreateCardFormData) =>
      cardsApi.createCard({ ...data, list_id: listId }),
    onSuccess: () => {
      // Invalidate any board queries containing this list
      queryClient.invalidateQueries({ queryKey: ['board'] })
      reset()
      onClose()
    },
  })

  const handleFormSubmit = (data: CreateCardFormData) => {
    const payload: CreateCardFormData = {
      ...data,
      // Convert empty strings to undefined so backend Optional[date] validates
      due_date: data.due_date && data.due_date.trim() !== '' ? data.due_date : undefined,
      description: data.description && data.description.trim() !== '' ? data.description : undefined,
    }
    createCardMutation.mutate(payload)
  }

  const handleClose = () => {
    reset()
    onClose()
  }

  return (
    <Dialog open={isOpen} onClose={handleClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/25" aria-hidden="true" />
      
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="mx-auto max-w-md rounded bg-white p-6">
          <div className="flex items-center justify-between mb-4">
            <Dialog.Title className="text-lg font-medium text-gray-900">
              Create New Card
            </Dialog.Title>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>

          <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-700">
                Card Title
              </label>
              <input
                {...register('title')}
                type="text"
                className={`input mt-1 ${errors.title ? 'border-red-300' : ''}`}
                placeholder="Enter card title"
              />
              {errors.title && (
                <p className="mt-1 text-sm text-red-600">{errors.title.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                Description (optional)
              </label>
              <textarea
                {...register('description')}
                rows={3}
                className={`input mt-1 ${errors.description ? 'border-red-300' : ''}`}
                placeholder="Enter card description"
              />
              {errors.description && (
                <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="due_date" className="block text-sm font-medium text-gray-700">
                Due Date (optional)
              </label>
              <input
                {...register('due_date')}
                type="date"
                className={`input mt-1 ${errors.due_date ? 'border-red-300' : ''}`}
              />
              {errors.due_date && (
                <p className="mt-1 text-sm text-red-600">{errors.due_date.message}</p>
              )}
            </div>

            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={handleClose}
                className="btn btn-secondary"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isLoading || createCardMutation.isPending}
                className="btn btn-primary"
              >
                {isLoading || createCardMutation.isPending ? 'Creating...' : 'Create Card'}
              </button>
            </div>
          </form>
        </Dialog.Panel>
      </div>
    </Dialog>
  )
}

