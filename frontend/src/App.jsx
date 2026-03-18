import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import ProfessorDashboard from './pages/ProfessorDashboard';
import StudentDashboard from './pages/StudentDashboard';

// Simple check to see if user is logged in
const ProtectedRoute = ({ children, allowedRole }) => {
  const token = localStorage.getItem('token');
  const role = localStorage.getItem('role');

  if (!token) return <Navigate to="/" />;
  if (allowedRole && role !== allowedRole) return <Navigate to="/" />;
  
  return children;
};

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        
        <Route 
          path="/professor" 
          element={
            <ProtectedRoute allowedRole="professor">
              <ProfessorDashboard />
            </ProtectedRoute>
          } 
        />

        <Route 
          path="/student" 
          element={
            <ProtectedRoute allowedRole="student">
              <StudentDashboard />
            </ProtectedRoute>
          } 
        />
      </Routes>
    </Router>
  );
}

export default App;