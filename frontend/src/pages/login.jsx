import React, { useState } from 'react';
import api from '../api';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async (e) => {
  e.preventDefault();
  try {
    // Standard Login Logic for OAuth2
    const formData = new URLSearchParams();
    formData.append('username', email); // backend expects 'username'
    formData.append('password', password);

    const res = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });

    localStorage.setItem('token', res.data.access_token);
    localStorage.setItem('role', res.data.role);
    
    // Redirect based on role
    window.location.href = res.data.role === 'professor' ? '/professor' : '/student';
  } catch (err) {
    console.error(err);
    alert("Login failed. Check your NITJ credentials.");
  }
};

  return (
    <div className="flex min-h-screen items-center justify-center">
      <form onSubmit={handleLogin} className="w-96 p-8 bg-white rounded-xl shadow-lg border border-slate-200">
        <h2 className="text-2xl font-bold mb-6 text-center text-indigo-600">Assignment Master</h2>
        <input 
          type="email" placeholder="NITJ Email" 
          className="w-full p-3 mb-4 border rounded"
          onChange={(e) => setEmail(e.target.value)} 
        />
        <input 
          type="password" placeholder="Password" 
          className="w-full p-3 mb-6 border rounded"
          onChange={(e) => setPassword(e.target.value)} 
        />
        <button className="w-full bg-indigo-600 text-white p-3 rounded font-bold hover:bg-indigo-700 transition">
          Sign In
        </button>
      </form>
    </div>
  );
};

export default Login;