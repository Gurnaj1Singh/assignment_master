import React, { useEffect, useState } from 'react';
import { LogOut, Users, FileText, Share2 } from 'lucide-react';
import api from '../api';

const ProfessorDashboard = () => {
  const handleLogout = () => {
    localStorage.clear();
    window.location.href = '/';
  };

const [showModal, setShowModal] = useState(false);
const [className, setClassName] = useState('');

const createClass = async () => {
  try {
    const res = await api.post('/classrooms/create', { class_name: className });
    alert(`Class Created! Code: ${res.data.class_code}`);
    setShowModal(false);
    // You would typically refresh the class list here
  } catch (err) {
    alert("Error creating class");
  }
};

  return (
    <div className="min-h-screen flex bg-slate-50">
      {/* Sidebar */}
      <div className="w-64 bg-indigo-900 text-white p-6">
        <h1 className="text-xl font-bold mb-10">Assignment Master</h1>
        <nav className="space-y-4">
          <div className="flex items-center gap-3 p-2 hover:bg-indigo-800 rounded cursor-pointer">
            <Users size={20} /> Classrooms
          </div>
          <div className="flex items-center gap-3 p-2 hover:bg-indigo-800 rounded cursor-pointer">
            <Share2 size={20} /> Collusion Groups
          </div>
        </nav>
        <button onClick={handleLogout} className="mt-auto flex items-center gap-3 text-red-300 hover:text-red-100 p-2">
          <LogOut size={20} /> Logout
        </button>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-10">
        <header className="flex justify-between items-center mb-10">
          <h2 className="text-3xl font-bold text-slate-800">Welcome, Professor</h2>
        </header>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* We will map through your classrooms here later */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <h3 className="font-bold text-lg mb-2 text-indigo-600">AI & Robotics</h3>
            <p className="text-slate-500 text-sm mb-4">Code: CS301</p>
            <button className="text-indigo-600 font-semibold hover:underline">View Submissions →</button>
          </div>
        </div>

        {/* Trigger Button */}
        <button 
        onClick={() => setShowModal(true)}
        className="bg-indigo-600 text-white px-4 py-2 rounded-lg font-bold hover:bg-indigo-700"
        >
        + New Classroom
        </button>

        {/* Simple Modal Overlay */}
        {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
            <div className="bg-white p-8 rounded-xl w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Create New Classroom</h2>
            <input 
                type="text" 
                placeholder="e.g. Robotics & AI" 
                className="w-full p-2 border rounded mb-6"
                onChange={(e) => setClassName(e.target.value)}
            />
            <div className="flex justify-end gap-3">
                <button onClick={() => setShowModal(false)} className="px-4 py-2 text-slate-600">Cancel</button>
                <button onClick={createClass} className="px-4 py-2 bg-indigo-600 text-white rounded">Create</button>
            </div>
            </div>
        </div>
        )}
      </div>


    </div>
  );
};

export default ProfessorDashboard;