import React, { useState } from 'react';
import { Upload, Plus, LogOut, CheckCircle } from 'lucide-react';
import api from '../api';

const StudentDashboard = () => {
  const [classCode, setClassCode] = useState('');
  const [joinedClasses, setJoinedClasses] = useState([]); // In a real app, fetch this on mount

  const joinClass = async () => {
    try {
      // Assuming you have a /classrooms/join endpoint
      await api.post('/classrooms/join', { code: classCode });
      alert("Successfully joined the class!");
      // Refresh logic here
    } catch (err) {
      alert("Invalid code or already joined.");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-4xl mx-auto">
        <header className="flex justify-between items-center mb-10">
          <h1 className="text-3xl font-bold text-slate-800">Student Portal</h1>
          <button onClick={() => {localStorage.clear(); window.location.href='/';}} className="text-red-500 flex items-center gap-2">
            <LogOut size={18} /> Logout
          </button>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Join Class Section */}
          <div className="md:col-span-1 bg-white p-6 rounded-2xl shadow-sm border border-slate-200 h-fit">
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
              <Plus className="text-indigo-600" /> Join Classroom
            </h2>
            <input 
              type="text" placeholder="6-digit code" 
              className="w-full p-2 border rounded mb-3 text-center uppercase font-mono"
              maxLength={6}
              onChange={(e) => setClassCode(e.target.value)}
            />
            <button onClick={joinClass} className="w-full bg-indigo-600 text-white py-2 rounded-lg font-semibold hover:bg-indigo-700 transition">
              Join
            </button>
          </div>

          {/* Assignments List */}
          <div className="md:col-span-2 space-y-4">
            <h2 className="text-lg font-bold mb-4">Pending Assignments</h2>
            {/* Example Assignment Card */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 flex justify-between items-center">
              <div>
                <h3 className="font-bold text-slate-800">CS301: NLP Research Paper</h3>
                <p className="text-sm text-slate-500">Deadline: March 1st, 2026</p>
              </div>
              <button className="bg-slate-100 text-indigo-600 px-4 py-2 rounded-lg font-bold hover:bg-indigo-600 hover:text-white transition flex items-center gap-2">
                <Upload size={18} /> Submit PDF
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StudentDashboard;