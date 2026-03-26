import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  CheckSquare, Plus, MoreVertical, Trash2, 
  Edit, Clock, AlertCircle, Check, ChevronDown, ChevronRight
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { tasksAPI } from '../lib/api';
import { toast } from 'sonner';

const PRIORITY_COLORS = {
  low: 'bg-gray-500/10 text-gray-400 border-gray-500/20',
  medium: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  high: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  urgent: 'bg-red-500/10 text-red-400 border-red-500/20'
};

const STATUS_ICONS = {
  todo: CheckSquare,
  in_progress: Clock,
  done: Check
};

export default function Tasks() {
  const { t } = useTranslation();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [doneCollapsed, setDoneCollapsed] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium',
    status: 'todo',
    due_date: ''
  });

  useEffect(() => {
    loadTasks();
  }, []);

  const loadTasks = async () => {
    try {
      const response = await tasksAPI.list();
      setTasks(response.data);
    } catch (error) {
      console.error('Failed to load tasks:', error);
      toast.error('Failed to load tasks');
    }
    setLoading(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = { ...formData };
      if (data.due_date) {
        data.due_date = new Date(data.due_date).toISOString();
      } else {
        delete data.due_date;
      }
      
      if (editingTask) {
        await tasksAPI.update(editingTask.id, data);
        toast.success('Task updated');
      } else {
        await tasksAPI.create(data);
        toast.success('Task created');
      }
      setIsDialogOpen(false);
      setEditingTask(null);
      setFormData({ title: '', description: '', priority: 'medium', status: 'todo', due_date: '' });
      loadTasks();
    } catch (error) {
      toast.error('Failed to save task');
    }
  };

  const handleEdit = (task) => {
    setEditingTask(task);
    setFormData({
      title: task.title,
      description: task.description || '',
      priority: task.priority,
      status: task.status,
      due_date: task.due_date ? task.due_date.split('T')[0] : ''
    });
    setIsDialogOpen(true);
  };

  const handleDelete = async (id) => {
    try {
      await tasksAPI.delete(id);
      toast.success('Task deleted');
      loadTasks();
    } catch (error) {
      toast.error('Failed to delete task');
    }
  };

  const toggleComplete = async (task) => {
    try {
      const newStatus = task.status === 'done' ? 'todo' : 'done';
      await tasksAPI.update(task.id, { ...task, status: newStatus });
      loadTasks();
    } catch (error) {
      toast.error('Failed to update task');
    }
  };

  const groupedTasks = {
    todo: tasks.filter(t => t.status === 'todo'),
    in_progress: tasks.filter(t => t.status === 'in_progress'),
    done: tasks.filter(t => t.status === 'done')
  };

  return (
    <div className="page-container" data-testid="tasks-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">{t('tasks.title')}</h1>
          <p className="text-gray-400 text-sm">{tasks.length} {t('tasks.title').toLowerCase()}</p>
        </div>
        
        <Button
          onClick={() => {
            setEditingTask(null);
            setFormData({ title: '', description: '', priority: 'medium', status: 'todo', due_date: '' });
            setIsDialogOpen(true);
          }}
          className="btn-primary flex items-center gap-2"
          data-testid="create-task-btn"
        >
          <Plus className="w-4 h-4" />
          {t('tasks.create')}
        </Button>
      </div>

      {/* Tasks Board */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin w-8 h-8 border-2 border-white/20 border-t-white rounded-full" />
        </div>
      ) : tasks.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-20"
        >
          <div className="w-16 h-16 bg-white/5 rounded-xl flex items-center justify-center mx-auto mb-4">
            <CheckSquare className="w-8 h-8 text-gray-600" />
          </div>
          <h3 className="text-lg font-medium text-white mb-2">{t('tasks.noTasks')}</h3>
        </motion.div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {Object.entries(groupedTasks).map(([status, statusTasks]) => {
            const StatusIcon = STATUS_ICONS[status];
            const isDone = status === 'done';
            const isCollapsed = isDone && doneCollapsed;
            
            return (
              <div key={status} className="space-y-4">
                <div 
                  className={`flex items-center gap-2 px-2 ${isDone ? 'cursor-pointer hover:bg-white/5 rounded-lg py-1 -my-1' : ''}`}
                  onClick={isDone ? () => setDoneCollapsed(!doneCollapsed) : undefined}
                >
                  {isDone && (
                    isCollapsed ? (
                      <ChevronRight className="w-4 h-4 text-gray-400" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-gray-400" />
                    )
                  )}
                  <StatusIcon className="w-4 h-4 text-gray-400" />
                  <h3 className="text-sm font-medium text-gray-400 uppercase">
                    {t(`tasks.${status === 'in_progress' ? 'inProgress' : status}`)}
                  </h3>
                  <span className="text-xs text-gray-600">({statusTasks.length})</span>
                  {isDone && statusTasks.length > 0 && (
                    <span className="text-xs text-gray-600 ml-auto">
                      {isCollapsed ? 'Aufklappen' : 'Einklappen'}
                    </span>
                  )}
                </div>
                
                <AnimatePresence>
                  {!isCollapsed && (
                    <motion.div 
                      className="space-y-3"
                      initial={isDone ? { opacity: 0, height: 0 } : false}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                    >
                      {statusTasks.map((task, index) => (
                    <motion.div
                      key={task.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className={`bg-[#121212] border border-white/5 rounded-xl p-4 hover:border-white/10 transition-colors group ${
                        task.status === 'done' ? 'opacity-60' : ''
                      }`}
                      data-testid={`task-item-${index}`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <button
                          onClick={() => toggleComplete(task)}
                          className={`mt-0.5 w-5 h-5 rounded border flex-shrink-0 flex items-center justify-center transition-colors ${
                            task.status === 'done' 
                              ? 'bg-green-500/20 border-green-500/30 text-green-400' 
                              : 'border-white/20 hover:border-white/40'
                          }`}
                        >
                          {task.status === 'done' && <Check className="w-3 h-3" />}
                        </button>
                        
                        <div className="flex-1 min-w-0">
                          <h4 className={`text-white font-medium text-sm ${
                            task.status === 'done' ? 'line-through' : ''
                          }`}>
                            {task.title}
                          </h4>
                          
                          {task.description && (
                            <p className="text-gray-500 text-xs mt-1 line-clamp-2">{task.description}</p>
                          )}
                          
                          <div className="flex items-center gap-2 mt-3">
                            <span className={`px-2 py-0.5 rounded text-xs border ${PRIORITY_COLORS[task.priority]}`}>
                              {t(`tasks.${task.priority}`)}
                            </span>
                            
                            {task.due_date && (
                              <span className="flex items-center gap-1 text-xs text-gray-500">
                                <Clock className="w-3 h-3" />
                                {new Date(task.due_date).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                        </div>
                        
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm" className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity">
                              <MoreVertical className="w-4 h-4 text-gray-400" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="bg-[#1A1A1A] border-white/10">
                            <DropdownMenuItem 
                              onClick={() => handleEdit(task)}
                              className="text-gray-300 focus:bg-white/10"
                            >
                              <Edit className="w-4 h-4 mr-2" /> {t('common.edit')}
                            </DropdownMenuItem>
                            <DropdownMenuItem 
                              onClick={() => handleDelete(task.id)}
                              className="text-red-400 focus:bg-red-500/10"
                            >
                              <Trash2 className="w-4 h-4 mr-2" /> {t('common.delete')}
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </motion.div>
                  ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
            );
          })}
        </div>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="bg-[#121212] border-white/10 text-white">
          <DialogHeader>
            <DialogTitle>{editingTask ? t('common.edit') : t('tasks.create')}</DialogTitle>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label className="text-gray-300">Title *</Label>
              <Input
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="mt-1 bg-black/30 border-white/10 text-white"
                required
                data-testid="task-title-input"
              />
            </div>
            
            <div>
              <Label className="text-gray-300">Description</Label>
              <Textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="mt-1 bg-black/30 border-white/10 text-white"
                rows={3}
                data-testid="task-description-input"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-gray-300">{t('tasks.priority')}</Label>
                <Select
                  value={formData.priority}
                  onValueChange={(value) => setFormData({ ...formData, priority: value })}
                >
                  <SelectTrigger className="mt-1 bg-black/30 border-white/10 text-white" data-testid="task-priority-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-[#1A1A1A] border-white/10">
                    <SelectItem value="low">{t('tasks.low')}</SelectItem>
                    <SelectItem value="medium">{t('tasks.medium')}</SelectItem>
                    <SelectItem value="high">{t('tasks.high')}</SelectItem>
                    <SelectItem value="urgent">{t('tasks.urgent')}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label className="text-gray-300">{t('tasks.status')}</Label>
                <Select
                  value={formData.status}
                  onValueChange={(value) => setFormData({ ...formData, status: value })}
                >
                  <SelectTrigger className="mt-1 bg-black/30 border-white/10 text-white" data-testid="task-status-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-[#1A1A1A] border-white/10">
                    <SelectItem value="todo">{t('tasks.todo')}</SelectItem>
                    <SelectItem value="in_progress">{t('tasks.inProgress')}</SelectItem>
                    <SelectItem value="done">{t('tasks.done')}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div>
              <Label className="text-gray-300">{t('tasks.dueDate')}</Label>
              <Input
                type="date"
                value={formData.due_date}
                onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                className="mt-1 bg-black/30 border-white/10 text-white"
                data-testid="task-duedate-input"
              />
            </div>
            
            <div className="flex justify-end gap-3 pt-4">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setIsDialogOpen(false)}
                className="text-gray-400"
              >
                {t('common.cancel')}
              </Button>
              <Button type="submit" className="btn-primary" data-testid="save-task-btn">
                {t('common.save')}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
