import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { 
  Calendar as CalendarIcon, Plus, ChevronLeft, ChevronRight,
  Clock, MapPin, MoreVertical, Trash2, Edit
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Calendar as CalendarComponent } from '../components/ui/calendar';
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
import { eventsAPI } from '../lib/api';
import { toast } from 'sonner';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isSameDay, addMonths, subMonths } from 'date-fns';
import { de, enUS } from 'date-fns/locale';

export default function Calendar() {
  const { t, i18n } = useTranslation();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingEvent, setEditingEvent] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    start_time: '',
    end_time: '',
    all_day: false,
    location: '',
    create_task: false
  });

  const locale = i18n.language === 'de' ? de : enUS;

  useEffect(() => {
    loadEvents();
  }, []);

  const loadEvents = async () => {
    try {
      const response = await eventsAPI.list();
      setEvents(response.data);
    } catch (error) {
      console.error('Failed to load events:', error);
      toast.error('Failed to load events');
    }
    setLoading(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = {
        title: formData.title,
        description: formData.description || null,
        start_time: new Date(formData.start_time).toISOString(),
        end_time: new Date(formData.end_time).toISOString(),
        all_day: formData.all_day,
        location: formData.location || null,
        create_task: formData.create_task
      };
      
      if (editingEvent) {
        await eventsAPI.update(editingEvent.id, data);
        toast.success('Event updated');
      } else {
        await eventsAPI.create(data);
        toast.success('Event created');
      }
      setIsDialogOpen(false);
      setEditingEvent(null);
      resetForm();
      loadEvents();
    } catch (error) {
      toast.error('Failed to save event');
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      start_time: '',
      end_time: '',
      all_day: false,
      location: '',
      create_task: false
    });
  };

  const handleEdit = (event) => {
    setEditingEvent(event);
    setFormData({
      title: event.title,
      description: event.description || '',
      start_time: event.start_time?.slice(0, 16) || '',
      end_time: event.end_time?.slice(0, 16) || '',
      all_day: event.all_day,
      location: event.location || ''
    });
    setIsDialogOpen(true);
  };

  const handleDelete = async (id) => {
    try {
      await eventsAPI.delete(id);
      toast.success('Event deleted');
      loadEvents();
    } catch (error) {
      toast.error('Failed to delete event');
    }
  };

  const handleDateClick = (date) => {
    setSelectedDate(date);
    const dateStr = format(date, 'yyyy-MM-dd');
    setFormData({
      ...formData,
      start_time: `${dateStr}T09:00`,
      end_time: `${dateStr}T10:00`
    });
  };

  const getEventsForDate = (date) => {
    return events.filter(event => {
      const eventDate = new Date(event.start_time);
      return isSameDay(eventDate, date);
    });
  };

  const monthStart = startOfMonth(currentMonth);
  const monthEnd = endOfMonth(currentMonth);
  const daysInMonth = eachDayOfInterval({ start: monthStart, end: monthEnd });

  // Add padding days
  const startPadding = monthStart.getDay();
  const paddedDays = Array(startPadding).fill(null).concat(daysInMonth);

  return (
    <div className="page-container" data-testid="calendar-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">{t('calendar.title')}</h1>
          <p className="text-gray-400 text-sm">{events.length} events</p>
        </div>
        
        <Button
          onClick={() => {
            setEditingEvent(null);
            resetForm();
            handleDateClick(selectedDate);
            setIsDialogOpen(true);
          }}
          className="btn-primary flex items-center gap-2"
          data-testid="create-event-btn"
        >
          <Plus className="w-4 h-4" />
          {t('calendar.newEvent')}
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin w-8 h-8 border-2 border-white/20 border-t-white rounded-full" />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Calendar Grid */}
          <div className="lg:col-span-8">
            <div className="bg-[#121212] border border-white/5 rounded-xl p-6">
              {/* Month Navigation */}
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-white">
                  {format(currentMonth, 'MMMM yyyy', { locale })}
                </h2>
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}
                    className="text-gray-400 hover:text-white"
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setCurrentMonth(new Date())}
                    className="text-gray-400 hover:text-white"
                  >
                    {t('calendar.today')}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}
                    className="text-gray-400 hover:text-white"
                  >
                    <ChevronRight className="w-5 h-5" />
                  </Button>
                </div>
              </div>

              {/* Day Headers */}
              <div className="grid grid-cols-7 gap-1 mb-2">
                {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                  <div key={day} className="text-center text-xs text-gray-500 py-2">
                    {day}
                  </div>
                ))}
              </div>

              {/* Calendar Days */}
              <div className="grid grid-cols-7 gap-1">
                {paddedDays.map((day, index) => {
                  if (!day) {
                    return <div key={`pad-${index}`} className="aspect-square" />;
                  }
                  
                  const dayEvents = getEventsForDate(day);
                  const isToday = isSameDay(day, new Date());
                  const isSelected = isSameDay(day, selectedDate);
                  
                  return (
                    <button
                      key={day.toISOString()}
                      onClick={() => handleDateClick(day)}
                      className={`
                        aspect-square p-1 rounded-lg text-sm transition-colors relative
                        ${isToday ? 'bg-blue-500/20 text-blue-400' : ''}
                        ${isSelected && !isToday ? 'bg-white/10 text-white' : ''}
                        ${!isToday && !isSelected ? 'hover:bg-white/5 text-gray-300' : ''}
                      `}
                    >
                      <span className={`${isToday ? 'font-bold' : ''}`}>
                        {format(day, 'd')}
                      </span>
                      {dayEvents.length > 0 && (
                        <div className="absolute bottom-1 left-1/2 -translate-x-1/2 flex gap-0.5">
                          {dayEvents.slice(0, 3).map((_, i) => (
                            <div key={i} className="w-1 h-1 rounded-full bg-blue-400" />
                          ))}
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Selected Day Events */}
          <div className="lg:col-span-4">
            <div className="bg-[#121212] border border-white/5 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4">
                {format(selectedDate, 'EEEE, d MMMM', { locale })}
              </h3>
              
              {getEventsForDate(selectedDate).length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  {t('calendar.noEvents')}
                </div>
              ) : (
                <div className="space-y-3">
                  {getEventsForDate(selectedDate).map((event) => (
                    <motion.div
                      key={event.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="bg-white/5 border border-white/10 rounded-lg p-4 group"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="text-white font-medium">{event.title}</h4>
                          {event.description && (
                            <p className="text-gray-500 text-sm mt-1">{event.description}</p>
                          )}
                          <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {format(new Date(event.start_time), 'HH:mm')}
                            </span>
                            {event.location && (
                              <span className="flex items-center gap-1">
                                <MapPin className="w-3 h-3" />
                                {event.location}
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
                              onClick={() => handleEdit(event)}
                              className="text-gray-300 focus:bg-white/10"
                            >
                              <Edit className="w-4 h-4 mr-2" /> {t('common.edit')}
                            </DropdownMenuItem>
                            <DropdownMenuItem 
                              onClick={() => handleDelete(event.id)}
                              className="text-red-400 focus:bg-red-500/10"
                            >
                              <Trash2 className="w-4 h-4 mr-2" /> {t('common.delete')}
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="bg-[#121212] border-white/10 text-white">
          <DialogHeader>
            <DialogTitle>{editingEvent ? t('common.edit') : t('calendar.newEvent')}</DialogTitle>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label className="text-gray-300">Title *</Label>
              <Input
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="mt-1 bg-black/30 border-white/10 text-white"
                required
                data-testid="event-title-input"
              />
            </div>
            
            <div>
              <Label className="text-gray-300">Description</Label>
              <Textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="mt-1 bg-black/30 border-white/10 text-white"
                rows={2}
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-gray-300">Start *</Label>
                <Input
                  type="datetime-local"
                  value={formData.start_time}
                  onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                  className="mt-1 bg-black/30 border-white/10 text-white"
                  required
                  data-testid="event-start-input"
                />
              </div>
              <div>
                <Label className="text-gray-300">End *</Label>
                <Input
                  type="datetime-local"
                  value={formData.end_time}
                  onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                  className="mt-1 bg-black/30 border-white/10 text-white"
                  required
                  data-testid="event-end-input"
                />
              </div>
            </div>
            
            <div>
              <Label className="text-gray-300">Location</Label>
              <Input
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                className="mt-1 bg-black/30 border-white/10 text-white"
                placeholder="Optional"
              />
            </div>
            
            <div className="flex items-center gap-3 py-2 px-3 bg-blue-500/5 border border-blue-500/10 rounded-lg">
              <input
                type="checkbox"
                id="create_task"
                checked={formData.create_task}
                onChange={(e) => setFormData({ ...formData, create_task: e.target.checked })}
                className="w-4 h-4 rounded border-white/20 bg-black/30 text-purple-500"
                data-testid="create-task-checkbox"
              />
              <label htmlFor="create_task" className="text-gray-300 text-sm cursor-pointer">
                Auch als Aufgabe anlegen (Frist = Terminbeginn)
              </label>
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
              <Button type="submit" className="btn-primary" data-testid="save-event-btn">
                {t('common.save')}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
