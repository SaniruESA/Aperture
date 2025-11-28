'use client';
import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabaseClient';
import type { User } from '@supabase/supabase-js';
import { ChevronDownIcon, Bars3Icon, XMarkIcon, UserIcon, Cog6ToothIcon, ArrowRightOnRectangleIcon } from '@heroicons/react/24/solid';
import Logo from '@/components/Logo';
import { Fragment } from 'react';
import Link from 'next/link';
// Helper to get days in current month
function getDaysInMonth(year: number, month: number) {
  return Array.from({ length: new Date(year, month + 1, 0).getDate() }, (_, i) => i + 1);
}

// Convert UTC time from Supabase back to PST/PDT for display
// NOT NEEDED - JUST RETURNS THE ORIGINAL DATE WHICH IS PST
function convertUTCToPST(utcDateString: string) {
  const utcDate = new Date(utcDateString);
  return utcDate;

  // // Get the timezone offset for the current date to determine if it's PST or PDT
  // const january = new Date(utcDate.getFullYear(), 0, 1);
  // const july = new Date(utcDate.getFullYear(), 6, 1);
  // const isPST = utcDate.getTimezoneOffset() > Math.min(january.getTimezoneOffset(), july.getTimezoneOffset());
  
  // // PST is UTC-8, PDT is UTC-7
  // const pstOffset = isPST ? 8 : 7;
  
  // // Convert from UTC to PST/PDT by subtracting the offset
  // const pstDate = new Date(utcDate.getTime() - (pstOffset * 60 * 60 * 1000));
  
  // return pstDate;
}

// New: Simple RegisterPopup for registration guidance
function RegisterPopup({ open, message, registrationType, onClose }: { open: boolean, message: string, registrationType: string, onClose: () => void }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 animate-fade-in">
      <div className="bg-[#181e29] rounded-2xl shadow-2xl border border-[#232a3a] p-8 w-full max-w-md relative flex flex-col items-center gap-4">
        <button
          className="absolute top-4 right-4 text-gray-400 hover:text-white text-2xl font-bold focus:outline-none cursor-pointer"
          onClick={onClose}
          aria-label="Close"
        >
          &times;
        </button>
        <div className="text-2xl font-bold text-white mb-2">Register for {registrationType}</div>
        <div className="text-gray-300 mb-4 text-center">{message}</div>
        <a
          href="/register"
          className="w-full py-2 rounded-lg bg-gradient-to-r from-blue-500 to-violet-500 text-white font-semibold shadow hover:from-blue-600 hover:to-violet-600 transition text-center"
        >
          Go to Registration
        </a>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [navOpen, setNavOpen] = useState(false);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; event: any } | null>(null);
  const [tooltipTimeout, setTooltipTimeout] = useState<NodeJS.Timeout | null>(null);
  const calendarRef = useRef<HTMLDivElement>(null);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [showRegisterPopup, setShowRegisterPopup] = useState(false);
  const [registerLoading, setRegisterLoading] = useState(false);
  const [userEvents, setUserEvents] = useState<any[]>([]);
  const [availableEvents, setAvailableEvents] = useState<any[]>([]);
  const [upcomingEvents, setUpcomingEvents] = useState<any[]>([]);
  const [announcements, setAnnouncements] = useState<any[]>([]);
  const [isAdmin, setIsAdmin] = useState(false);
  const [showAddAnnouncement, setShowAddAnnouncement] = useState(false);
  const [newAnnouncement, setNewAnnouncement] = useState({
    title: '',
    date: '',
    description: ''
  });
  const [savingAnnouncement, setSavingAnnouncement] = useState(false);
  const [email, setEmail] = useState<string | null>(null);
  const [registerPopupMessage, setRegisterPopupMessage] = useState<string | null>(null);
  const [registerPopupType, setRegisterPopupType] = useState<string>('');
  const [clubRegistrationOpenDate, setClubRegistrationOpenDate] = useState<Date | null>(null);
  const [clubRegistrationCloseDate, setClubRegistrationCloseDate] = useState<Date | null>(null);
  const [eventRegistrationOpenDate, setEventRegistrationOpenDate] = useState<Date | null>(null);
  const [eventRegistrationCloseDate, setEventRegistrationCloseDate] = useState<Date | null>(null);

  // Fetch available events from master_competitive_events
  useEffect(() => {
    const fetchEvents = async () => {
      const { data, error } = await supabase
        .from('master_competitive_events')
        .select('id, name');
      if (!error && data) {
        setAvailableEvents(data);
      }
    };
    fetchEvents();
  }, []);

  // Fetch real upcoming events from Supabase
  useEffect(() => {
    const fetchUpcomingEvents = async () => {
      const { data, error } = await supabase
        .from('calendar')
        .select('id, event, date, type, urgency, description, location')
        .order('date', { ascending: true });
      if (!error && data) {
        const now = new Date();
        const filtered = data.filter(e => {
          const eventDate = new Date(e.date);
          // If event is in the future, include
          if (eventDate > now) return true;
          // If event is today (regardless of time), include
          return eventDate.getFullYear() === now.getFullYear() &&
                 eventDate.getMonth() === now.getMonth() &&
                 eventDate.getDate() === now.getDate();
        });
        setUpcomingEvents(filtered);
      }
    };
    fetchUpcomingEvents();
  }, []);

  // Fetch real announcements from Supabase
  useEffect(() => {
    const fetchAnnouncements = async () => {
      const { data, error } = await supabase
        .from('announcements')
        .select('id, title, date, description')
        .order('date', { ascending: false });
      if (!error && data) {
        setAnnouncements(data);
      }
    };
    fetchAnnouncements();
  }, []);

  // Check if user is admin
  useEffect(() => {
    const checkAdmin = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      if (user) {
        const { data: profile, error } = await supabase
          .from('profiles')
          .select('admin')
          .eq('id', user.id)
          .single();
        if (!error && profile && profile.admin === true) {
          setIsAdmin(true);
        } else {
          setIsAdmin(false);
        }
      } else {
        setIsAdmin(false);
      }
    };
    checkAdmin();
  }, []);

  useEffect(() => {
    const fetchDeadlines = async () => {
      const { data: deadlines, error } = await supabase
        .from('registrationDeadlines')
        .select('deadline, date');
      if (!error && deadlines) {
        deadlines.forEach((row: { deadline: string; date: string }) => {
          // Parse as PST (America/Los_Angeles)
          const localDate = new Date(row.date + 'T00:00:00-08:00');
          if (row.deadline === 'Club Registration Open') setClubRegistrationOpenDate(localDate);
          if (row.deadline === 'Club Registration Close') setClubRegistrationCloseDate(localDate);
          if (row.deadline === 'Event Registration Open') setEventRegistrationOpenDate(localDate);
          if (row.deadline === 'Event Registration Close') setEventRegistrationCloseDate(localDate);
        });
      }
    };
    fetchDeadlines();
  }, []);

  useEffect(() => {
    const fetchUserAndEvents = async () => {
      const { data, error } = await supabase.auth.getUser();
      if (error || !data.user) {
        router.replace('/signin');
        setLoading(false);
        return;
      }
      setUser(data.user);
      // Fetch user events and email from profiles table
      const { data: profile, error: profileError } = await supabase
        .from('profiles')
        .select('events, email')
        .eq('id', data.user.id)
        .single();
      if (!profileError && profile) {
        setUserEvents(Array.isArray(profile.events) ? profile.events : []);
        setEmail(profile.email || '');
        // Registration popup logic
        const now = new Date();
        const eventRegOpen = eventRegistrationOpenDate && eventRegistrationCloseDate && now >= eventRegistrationOpenDate && now <= eventRegistrationCloseDate;
        if ((Array.isArray(profile.events) ? profile.events.length : 0) < 1 && eventRegOpen) {
          setRegisterPopupMessage('You haven\'t registered for any competitive events yet. Please do so here.');
          setRegisterPopupType('events');
        } else {
          setRegisterPopupMessage(null);
          setRegisterPopupType('');
        }
      } else {
        setUserEvents([]);
        setEmail('');
        setRegisterPopupMessage(null);
        setRegisterPopupType('');
      }
      setLoading(false);
    };
    fetchUserAndEvents();
  }, [router, eventRegistrationOpenDate, eventRegistrationCloseDate]);

  // Cleanup tooltip timeout on unmount
  useEffect(() => {
    return () => {
      if (tooltipTimeout) {
        clearTimeout(tooltipTimeout);
      }
    };
  }, [tooltipTimeout]);

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    router.replace('/signin');
  };

  const handleViewEventDetails = (event: any) => {
    // Navigate to calendar page with event details
    router.push(`/calendar?event=${event.id}`);
  };

  const handleRegisterEvents = async (selected: any[]) => {
    setRegisterLoading(true);
    if (!user) return;
    // Store selected event objects (id and name) in the user's events array
    const selectedEventObjs = availableEvents.filter(e => selected.includes(e.name));
    const { error } = await supabase
      .from('profiles')
      .update({ events: selectedEventObjs })
      .eq('id', user.id);
    if (!error) {
      setUserEvents(selectedEventObjs);
      setShowRegisterPopup(false);
    }
    setRegisterLoading(false);
  };

  if (loading) return <div className="flex justify-center items-center h-screen">Loading...</div>;

  // Placeholder for user's name
  const userName = user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'Member';

  // Calendar logic
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth();
  const days = getDaysInMonth(year, month);
  // Use upcomingEvents for the timeline
  const timelineEvents = upcomingEvents.filter(e => {
    const eventDate = new Date(e.date);
    return eventDate.getFullYear() === year && eventDate.getMonth() === month;
  });
  const eventDates = timelineEvents.map(e => new Date(e.date).getDate());
  const eventMap = Object.fromEntries(
    timelineEvents.map(e => [new Date(e.date).getDate(), e])
  );

  return (
    <div className="min-h-screen bg-[#0a101f] text-white flex flex-col">
      <RegisterPopup
        open={!!registerPopupMessage}
        message={registerPopupMessage || ''}
        registrationType={registerPopupType}
        onClose={() => setRegisterPopupMessage(null)}
      />

      {/* Spacer for nav */}
      <div className="h-32" />

      <div className="flex flex-col lg:flex-row gap-8 px-4 pb-8 max-w-5xl w-full mx-auto">
        {/* Main Content */}
        <div className="flex-1 flex flex-col gap-8">
          {/* Welcome Section */}
          <div
            className="bg-[#181e29] rounded-2xl p-6 shadow-lg border border-[#232a3a] relative"
            style={{ boxShadow: '0 0 10px 0 #3b82f6, 0 0 24px 0 #8b5cf6, 0 0 0 1px #232a3a' }}
          >
            <h1 className="text-2xl sm:text-3xl font-bold mb-2">Welcome back, {userName}!</h1>
            <p className="text-gray-400">Here's what's happening in TSA.</p>
          </div>

          {/* Upcoming Events Card */}
          <div
            className="bg-[#181e29] rounded-2xl p-6 shadow-lg border border-[#232a3a] relative"
            style={{ boxShadow: '0 0 10px 0 #3b82f6, 0 0 24px 0 #8b5cf6, 0 0 0 1px #232a3a' }}
          >
            <h2 className="text-xl font-semibold mb-4">Upcoming Events</h2>
            {upcomingEvents.length > 0 ? (
              <ul className="space-y-4">
                {upcomingEvents.slice(0, 3).map(event => (
                  <li key={event.id} className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <div className="font-medium">{event.event}</div>
                      <div className="text-gray-400 text-sm">
                      {convertUTCToPST(event.date).toLocaleString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                        hour12: true
                      })}
                      </div>
                      {event.location && (
                        <div className="text-gray-500 text-xs mt-1">
                          📍 {event.location}
                        </div>
                      )}
                    </div>
                    <button 
                      onClick={() => handleViewEventDetails(event)}
                      className="mt-2 sm:mt-0 px-4 py-2 rounded-lg bg-gradient-to-r from-blue-500 to-violet-500 text-white font-semibold shadow hover:from-blue-600 hover:to-violet-600 transition cursor-pointer"
                    >
                      View Details
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-gray-400">No upcoming events — check back soon!</div>
            )}
          </div>

          {/* Quick Links Section */}
          <div
            className="flex flex-wrap gap-4 justify-between bg-[#181e29] rounded-2xl p-4 shadow-lg border border-[#232a3a] relative"
            style={{ boxShadow: '0 0 10px 0 #3b82f6, 0 0 24px 0 #8b5cf6, 0 0 0 1px #232a3a' }}
          >
            <button 
              onClick={() => router.push('/calendar')}
              className="flex-1 min-w-[140px] px-4 py-3 rounded-xl bg-[#232a3a] text-white font-semibold shadow hover:bg-blue-900/30 transition cursor-pointer"
            >
              View All Events
            </button>
            <button
              className="flex-1 min-w-[140px] px-4 py-3 rounded-xl bg-[#232a3a] text-white font-semibold shadow hover:bg-blue-900/30 transition cursor-pointer"
              onClick={() => router.push('/profile')}
            >
              My Profile
            </button>
            {/* disabled for now */}
            <button className="flex-1 min-w-[140px] px-4 py-3 rounded-xl bg-[#232a3a] text-white font-semibold shadow hover:bg-blue-900/30 transition cursor-pointer" onClick={() => router.push('/register')}>Register</button>
            <button className="flex-1 min-w-[140px] px-4 py-3 rounded-xl bg-[#232a3a] text-white font-semibold shadow hover:bg-blue-900/30 transition cursor-pointer" onClick={() => router.push('/contact')}>Contact Us</button>
          </div>
        </div>

        {/* Announcements Feed */}
        <div className="w-full lg:w-[340px] flex-shrink-0">
          <div
            className="bg-[#181e29] rounded-2xl p-6 shadow-lg border border-[#232a3a] h-full flex flex-col relative"
            style={{ boxShadow: '0 0 10px 0 #3b82f6, 0 0 24px 0 #8b5cf6, 0 0 0 1px #232a3a' }}
          >
            <h2 className="text-xl font-semibold mb-4">Announcements</h2>
            <div className="overflow-y-auto max-h-80 scrollbar-thin scrollbar-thumb-[#232a3a] scrollbar-track-transparent">
              {announcements.length > 0 ? (
                announcements.map(ann => (
                  <div key={ann.id} className="mb-6 last:mb-0">
                    <div className="font-medium mb-1">{ann.title}</div>
                    <div className="text-gray-400 text-xs mb-1">
                    {convertUTCToPST(ann.date).toLocaleString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                      hour12: true
                    })}
                    </div>
                    <div className="text-gray-300 text-sm line-clamp-2">{ann.description}</div>
                  </div>
                ))
              ) : (
                <div className="text-gray-400">No announcements yet.</div>
              )}
            </div>
            {isAdmin && (
              <div className="w-full flex justify-center mt-10">
                <button
                  className="px-4 py-2 rounded-lg bg-gradient-to-r from-blue-500 to-violet-500 text-white font-semibold shadow hover:from-blue-600 hover:to-violet-600 transition cursor-pointer"
                  onClick={() => setShowAddAnnouncement(true)}
                >
                  Add Announcement
                </button>
              </div>
            )}
            {/* Add Announcement Modal */}
            {showAddAnnouncement && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 animate-fade-in">
                <div className="bg-[#181e29] rounded-2xl shadow-2xl border border-[#232a3a] p-8 w-full max-w-md relative">
                  <button
                    className="absolute top-4 right-4 text-gray-400 hover:text-white text-2xl font-bold focus:outline-none"
                    onClick={() => setShowAddAnnouncement(false)}
                    aria-label="Close"
                  >
                    &times;
                  </button>
                  <div className="flex flex-col gap-4">
                    <div className="text-2xl font-bold text-white mb-2">Add Announcement</div>
                    <label className="text-sm font-medium text-white">Title</label>
                    <input
                      type="text"
                      className="w-full p-2 rounded-lg bg-[#232a3a] border border-[#3a4151] text-white"
                      value={newAnnouncement.title}
                      onChange={e => setNewAnnouncement({ ...newAnnouncement, title: e.target.value })}
                      placeholder="Announcement title"
                    />
                    <label className="text-sm font-medium text-white">Date & Time</label>
                    <input
                      type="datetime-local"
                      className="w-full p-2 rounded-lg bg-[#232a3a] border border-[#3a4151] text-white"
                      value={newAnnouncement.date}
                      onChange={e => setNewAnnouncement({ ...newAnnouncement, date: e.target.value })}
                    />
                    <label className="text-sm font-medium text-white">Description</label>
                    <textarea
                      className="w-full p-2 rounded-lg bg-[#232a3a] border border-[#3a4151] text-white"
                      value={newAnnouncement.description}
                      onChange={e => setNewAnnouncement({ ...newAnnouncement, description: e.target.value })}
                      placeholder="Announcement description"
                      rows={4}
                    />
                    <button
                      className="mt-4 w-full py-2 rounded-lg bg-gradient-to-r from-blue-500 to-violet-500 text-white font-semibold shadow hover:from-blue-600 hover:to-violet-600 transition disabled:opacity-50"
                      disabled={savingAnnouncement || !newAnnouncement.title || !newAnnouncement.date || !newAnnouncement.description}
                      onClick={async () => {
                        setSavingAnnouncement(true);
                        // Insert into Supabase with proper timezone handling
                        // The input datetime-local is in local timezone, we need to append the current timezone offset
                        const inputDate = new Date(newAnnouncement.date);
                        
                        // Determine if we're currently in PST (-08) or PDT (-07)
                        const january = new Date(inputDate.getFullYear(), 0, 1);
                        const july = new Date(inputDate.getFullYear(), 6, 1);
                        const isPST = inputDate.getTimezoneOffset() > Math.min(january.getTimezoneOffset(), july.getTimezoneOffset());
                        const timezoneOffset = isPST ? '-08' : '-07';
                        
                        // Format the date string with timezone offset for Supabase timestamptz
                        const dateWithTimezone = newAnnouncement.date + ':00' + timezoneOffset + ':00';

                        const { error } = await supabase
                          .from('announcements')
                          .insert([
                            {
                              title: newAnnouncement.title,
                              date: dateWithTimezone, // Store with timezone offset
                              description: newAnnouncement.description
                            }
                          ]);                        
                        setSavingAnnouncement(false);
                        if (!error) {
                          setShowAddAnnouncement(false);
                          setNewAnnouncement({ title: '', date: '', description: '' });
                          // Refresh announcements
                          const { data, error: fetchError } = await supabase
                            .from('announcements')
                            .select('id, title, date, description')
                            .order('date', { ascending: false });
                          if (!fetchError && data) {
                            setAnnouncements(data);
                          }
                        } else {
                          alert('Failed to add announcement.');
                        }
                      }}
                    >
                      {savingAnnouncement ? 'Saving...' : 'Save Announcement'}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Calendar Timeline */}
      <div className="w-full max-w-5xl mx-auto px-4 mb-4 mt-2">
        <div
          className="mb-2 text-lg font-semibold text-white px-2"
          style={{ textShadow: '0 0 2px #3b82f6, 0 0 4px #8b5cf6' }}
        >
          {now.toLocaleString('default', { month: 'long', year: 'numeric' })}
        </div>
        <div className='px-4 pt-4 pb-1 md:pb-4 rounded-2xl'
        style={{boxShadow: '0 0 10px 0 #3b82f6, 0 0 24px 0 #8b5cf6, 0 0 0 1px #232a3a' }}>
          <div
            ref={calendarRef}
            className="flex overflow-x-auto gap-2 md:pb-2 scrollbar-thin scrollbar-thumb-blue-900 scrollbar-track-transparent relative cursor-pointer mb-10 md:mb-0"
            style={{ WebkitOverflowScrolling: 'touch',}}
            onClick={() => router.push('/calendar')}
          >
            {days.map(day => {
              const isEvent = eventDates.includes(day);
              const event = eventMap[day];
              return (
                <div
                  key={day}
                  className={`flex flex-col items-center group relative cursor-pointer select-none`}
                  
                >
                  <div
                    className={`w-10 h-10 flex items-center justify-center rounded-full text-lg font-semibold cursor-pointer
                      ${isEvent ? 'bg-gradient-to-br from-blue-500 to-violet-500 text-white shadow-lg' : 'bg-[#232a3a] text-gray-300'}
                      border border-[#232a3a] transition hover:scale-105`}

                      onMouseEnter={e => {
                        if (isEvent) {
                          // Clear any existing timeout
                          if (tooltipTimeout) {
                            clearTimeout(tooltipTimeout);
                            setTooltipTimeout(null);
                          }
                          const rect = (e.target as HTMLElement).getBoundingClientRect();
                          setTooltip({ x: rect.left + rect.width / 2, y: rect.top, event });
                        }
                      }}
                      onMouseLeave={() => {
                        // Clear any existing timeout
                        if (tooltipTimeout) {
                          clearTimeout(tooltipTimeout);
                        }
                        // Add a small delay to prevent flickering when moving between elements
                        const timeout = setTimeout(() => setTooltip(null), 50);
                        setTooltipTimeout(timeout);
                      }}
                      onClick={e => {
                        e.stopPropagation(); // Prevent triggering the parent onClick
                        if (isEvent) {
                          router.push('/calendar');
                        }
                      }}
                  >
                    {day}
                  </div>
                  {isEvent && (
                    <div className="w-2 h-2 rounded-full bg-blue-400 mt-1" />
                  )}
                </div>
              );
            })}
          </div>
        </div>
        {/* Tooltip */}
        {tooltip && (
          <div
            className="fixed z-50 px-4 py-2 rounded-xl bg-[#232a3a] text-white shadow-lg border border-blue-500 text-sm pointer-events-none"
            style={{ 
              left: tooltip.x, 
              top: tooltip.y - 60, 
              transform: 'translate(-50%, 0)',
              transition: 'opacity 0.1s ease-in-out'
            }}
          >
            <div className="font-bold mb-1">{tooltip.event.event}</div>
            <div className="text-xs text-gray-300">
            {convertUTCToPST(tooltip.event.date).toLocaleString('en-US', {
              month: 'short',
              day: 'numeric',
              year: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
              hour12: true
            })}            
            </div>
            {tooltip.event.location && (
              <div className="text-xs text-blue-300 mt-1">
                📍 {tooltip.event.location}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
} 